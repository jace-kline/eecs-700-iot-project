import subprocess
import psutil
from time import sleep
from process_usage import process_metrics_generator
from multithreading import AccumulatorThread, stop_thread, stop_all_threads

class ProcessTester(object):
    def __init__(self):
        self.procs = []

    # spawns a root process with n children
    def spawn(self, n):
        p = subprocess.Popen(
            ["python3", "busy.py", f"{n}", "--root"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        sleep(0.5)
        parent = psutil.Process(p.pid)
        children = parent.children(recursive=True)
        self.procs = [parent, *children]
        return self.procs

    def __del__(self):
        for proc in self.procs:
            proc.kill()

def test_threaded_metrics():
    tester = ProcessTester()
    procs = tester.spawn(2)

    threads = [
        AccumulatorThread(gen=process_metrics_generator(proc), delay=2)
        for proc in procs
    ]

    for t in threads:
        t.start()

    sleep(10)
    stop_all_threads()
    results = [ t.join() for t in threads ]
    print(results)
    print(results[0])

def main():
    test_threaded_metrics()

if __name__ == "__main__":
    main()