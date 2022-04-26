import subprocess
import psutil
from time import sleep

# A wrapper class that optionally cleans up (kills) 
# the processes it launches when it goes out of scope
class ProcessRunner:
    def __init__(self, cmd, popen_kwargs={}, clean=True):
        self.cmd = cmd
        self.popen_kwargs = popen_kwargs
        self.clean = clean
        self.procs = []

    def run(self):
        self.procs = launch_process(self.cmd, self.popen_kwargs)
        return self.procs

    def __del__(self):
        if self.clean:
            for proc in self.procs:
                proc.kill()

# Launch a process and return the psutil Process objects
# of the parent and child processes
def launch_process(cmd, popen_kwargs={}):
    # splits the command string into Popen list of strings form
    # run the command, return a subprocess Process object
    p = subprocess.Popen(cmd.split(), **popen_kwargs)

    # construct psutil Process objects
    parent = psutil.Process(p.pid)
    children = parent.children(recursive=True)
    procs = [parent, *children]
    for proc in procs:
        print(proc.pid)
    print(len(procs))
    return procs

# launch Mosquitto broker
# return a list of Process objects that are spawned
def launch(port=1883, configpath=None):

    cmd = f"mosquitto -d -p {port}" \
    + (configpath if configpath is not None else "")

    proc_runner = ProcessRunner(cmd)
    procs = proc_runner.run()

    while True:
        sleep(3)

if __name__ == "__main__":
    launch()
