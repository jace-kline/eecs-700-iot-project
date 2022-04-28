import subprocess, psutil
from time import sleep

# Launch a process
def launch_process(cmd, popen_kwargs={}):
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
        popen = launch_process(cmd)
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

# launch Mosquitto broker
# return a list of Process objects that are spawned
def launch_broker(port=1883, configpath=None):

    cmd = f"mosquitto -d -p {port}" \
    + (configpath if configpath is not None else "")

    # launch the process
    popen = launch_process(cmd)

    # wait until the broker is ready
    

    # for proc in procs:
    #     print(proc.pid)
    #     proc.kill()


if __name__ == "__main__":
    launch_broker()
