import subprocess
import psutil
from time import sleep
from process_usage import process_metrics_generator
from multithreading import AccumulatorThread, stop_thread, stop_all_threads

def spawn():
    p = subprocess.Popen(["python3", "busy.py", "2", "--root"])
    sleep(1)
    parent = psutil.Process(p.pid)
    children = parent.children(recursive=True)
    return [parent, *children]

def clean(procs):
    for proc in procs:
        proc.kill()

def test_threaded_metrics():
    procs = spawn()

    threads = [
        AccumulatorThread(gen=process_metrics_generator, args=(proc, 1))
        for proc in procs
    ]

    for t in threads:
        t.start()

    sleep(10)
    stop_all_threads()
    results = [ t.join() for t in threads ]
    print(results)

    clean(procs)

def main():
    test_threaded_metrics()

if __name__ == "__main__":
    main()