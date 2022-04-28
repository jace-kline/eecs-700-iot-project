import subprocess, psutil, docker, logging
from time import sleep
from usage.metrics import *
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

# given command strings and process names,
# get all psutil.Process objects
def mk_processes(cmds=[], names=[], delay=0.5):
    # map pids to processes to avoid duplicates
    pidmap = {}

    procs = []
    # run commands and get resulting process objects
    for cmd in cmds:
        popen = launch_cmd(cmd)
        sleep(delay)
        procs += get_procs_recursive(popen.pid)

    sleep(delay)
    # add process objects gathered from names
    for name in names:
        procs += procs_from_name(name)

    # insert each into map, avoiding duplicates
    for proc in procs:
        pidmap[proc.pid] = pidmap.get(proc.pid, proc)

    return pidmap.values()

class CmdLauncher:
    def __init__(self, cmd, ready=(lambda: True), ps_names=[], clean=True):
        self.cmd = cmd
        self.ready = ready
        self.ps_names = ps_names
        self.clean = clean
        self.procs = []

    def launch(self):
        logger.info(f"Running command '{self.cmd}'")
        popen = launch_cmd(self.cmd)

        while not self.ready():
            sleep(0.1)

        self.procs = get_procs_recursive(popen.pid)
        return [ process_metrics_generator(proc) for proc in self.procs ]

    def clean(self):
        if self.clean:
            logger.info(f"Killing process (PID = {proc.pid}) (name = {proc.name()})")
            for proc in self.procs:
                proc.kill()

    def __del__(self):
        self.clean()

# takes a list of lists of generator results and merges the
# inner lists component-wise based on the time sampled
# i.e., [res[0][0] + res[1][0] + ..., res[0][1] + res[1][1] + ..., ...]
def merge_metrics(results):
    def transpose(ls):
        minlen = min([len(l) for l in ls])
        return [[l[i] for l in ls] for i in range(0, minlen)]

    return [ MetricsSample.merge_many(t) for t in transpose(results) ]

def run_scenario(clientfunc, launchers=[], sample_delay=2, track_containers=False, clean_containers=False):
    client = docker.from_env()
    ps_names = []
    gens = []
    # launch each launcher in order
    for launcher in launchers:
        # launch, wait till ready, and append generators
        gens += launcher.launch()

        # add the associated process names -> gens for the launch (no duplicates)
        for ps_name in launcher.ps_names:
            if ps_name not in ps_names:
                ps_names.append(ps_name)
                procs = procs_from_name(ps_name)
                launcher.procs += procs
                gens += [ process_metrics_generator(p) for p in procs ]

    # if tracking containers, create generators for all of them
    if track_containers:
        containers = client.containers.list()
        for c in containers:
            logger.info(f"Tracking container {c.name}")
        gens += [ container_metrics_generator(c) for c in containers ]

    # gather the metrics, running each generator in its own thread
    threads = [ AccumulatorThread(gen=gen, delay=sample_delay) for gen in gens ]
    logger.info(f"Running {len(threads)} metrics threads")
    for t in threads:
        t.start()

    # run the "client" that measures RTT stream for some amount of time
    rtts = clientfunc()
    
    # collect thread results & merge them by time step
    stop_all_threads()
    metrics = merge_metrics([ t.join() for t in threads ])

    # clean up
    for launcher in launchers:
        launcher.clean()

    if clean_containers:
        for c in client.containers.list():
            logger.info(f"Removing container {c.name}")
            c.stop()
            c.remove()

    return (metrics, rtts)
