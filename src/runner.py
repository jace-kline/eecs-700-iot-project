import subprocess, psutil, docker, logging
from time import sleep
from metrics import *
from multithreading import AccumulatorThread, stop_all_threads

logger = logging.getLogger("runner")

# Launch a process
def launch_cmd(cmd, popen_kwargs={}):
    # splits the command string into Popen list of strings form
    # run the command, return a subprocess Popen object
    return subprocess.Popen(cmd.split(), **popen_kwargs)

def get_procs_recursive(pid):
    try:
        parent = psutil.Process(pid)
    except psutil.NoSuchProcess:
        return []
    children = parent.children(recursive=True)
    return [parent, *children]

def pids_from_name(name):
    try:
        return [ int(pid) for pid in subprocess.check_output(["pidof", name]).split() ]
    except subprocess.CalledProcessError:
        return []

def procs_from_name(name):
    # get the Process + children Processes for each pid
    procs_ = [ get_procs_recursive(pid) for pid in pids_from_name(name) ]
    # flatten the list of lists into single list
    procs = []
    for proclist in procs_:
        procs += proclist
    return procs

class CmdLaunchError(Exception):
    pass


class CmdLauncher:
    def __init__(self, cmd, wait=(lambda: True)):
        self.cmd = cmd
        self.wait = wait

    def launch(self):
        logger.info(f"Running command '{self.cmd}'")
        popen = launch_cmd(self.cmd)

        # this will return when the cmd is "ready"
        running = self.wait()

        # if startup failed, return None as an Error
        if not running:
            raise CmdLaunchError(f"Failed to run command {self.cmd}")
        
        return get_procs_recursive(popen.pid)


class ScenarioRunner:
    def __init__(
        self,
        client_func, # the client function that returns RTT vals
        launchers=[], # the launcher structs that contain 'cmd' string and 'wait' function fields
        ps_names=[], # process names to track (outside of launchers)
        pids=[], # pids to track (outside of launchers)
        sample_delay=2, # delay between metrics samples
        track_containers=False, # should we track container stats?
        clean_containers=False # should we remove containers upon termination
    ):
        self.client_func = client_func
        self.launchers = launchers
        self.ps_names = ps_names
        self.pids = pids
        self.sample_delay = sample_delay
        self.track_containers = track_containers
        self.clean_containers = clean_containers

        self.docker_client = docker.from_env() if track_containers else None
        self.pid_proc_map = {}
        self.cleaned = False

    def run(self):
        def try_add_proc(proc):
            if proc.pid not in self.pid_proc_map:
                self.pid_proc_map[proc.pid] = proc

        # launch each launcher in order
        for launcher in self.launchers:
            try:
                procs = launcher.launch()
            # if any commands fail in launch sequence, clean up & exit
            except CmdLaunchError as e:
                logger.error(e)
                self.cleanup()
                exit(1)

            for proc in procs:
                try_add_proc(proc)

        # get the processes for the supplied process names
        for ps_name in self.ps_names:
            procs = procs_from_name(ps_name)
            for proc in procs:
                try_add_proc(proc)

        # get the processes for the supplied PIDs
        for pid in self.pids:
            procs = get_procs_recursive(pid)
            for proc in procs:
                try_add_proc(proc)

        # create metrics generators for all the spawned processes
        # ensure each is still "running" & permission is allowed
        gens = []
        for (pid, proc) in self.pid_proc_map.items():
            try:
                gens.append(process_metrics_generator(proc))
            except (psutil.AccessDenied, psutil.NoSuchProcess) as e:
                logger.warn(f"Could not create generator for PID={pid}. {e.msg}")
                del self.pid_proc_map[pid]

        # if tracking containers, create metrics generators for all of them
        if self.track_containers:
            containers = self.docker_client.containers.list()
            for c in containers:
                logger.info(f"Tracking container {c.name}")
            gens += [ container_metrics_generator(c) for c in containers ]

        # gather the metrics, running each generator in its own thread
        threads = [ AccumulatorThread(gen=gen, delay=self.sample_delay) for gen in gens ]
        logger.info(f"Running {len(threads)} metrics threads")
        for t in threads:
            t.start()

        # run the "client" that measures RTT stream for some amount of time
        logger.info("Starting client")
        rtts = self.client_func()
        
        # collect thread results & merge them by time step
        stop_all_threads()
        logger.info("Stopping threads")
        metrics = [ t.join() for t in threads if not t.err ]
        # merge metrics here??

        # return the collected values
        return (metrics, rtts)

    def cleanup(self):
        if not self.cleaned:
            for (pid, proc) in self.pid_proc_map.items():
                try:
                    proc.kill()
                    logger.info(f"Killed process (PID={pid}) (name={proc.name()})")
                except (psutil.AccessDenied, psutil.NoSuchProcess) as e:
                    logger.warn(f"Could not kill PID={pid}. {e.msg}")

            if self.clean_containers:
                for c in self.docker_client.containers.list():
                    c.stop()
                    c.remove()
                    logger.info(f"Removed container {c.name}")
            self.cleaned = True

    def __del__(self):
        self.cleanup()
