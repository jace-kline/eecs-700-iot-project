from argparse import ArgumentError
import concurrent.futures
import threading
import queue
import random
from time import sleep

# takes a generator function (with __next__() method)
# produces a thread object that continuously generates & stores values until...
# global/local terminate signal is set OR generator runs out of values
class AccumulatorThread(threading.Thread):
    # static termination stuff
    terminate = False

    def __init__(self, queue=None, gen=None, args=(), kwargs={}):
        if queue is None or gen is None:
            raise ArgumentError(argument=None, message="Must provide 'queue' and 'gen' arguments")
        threading.Thread.__init__(self)
        self._accum = []
        self._queue = queue
        self._gen = gen
        self._args = args
        self._kwargs = kwargs
    
    def _should_terminate(self):
        flag = (self._queue.get() is None) if not self._queue.empty() else False
        return AccumulatorThread.terminate or flag

    def run(self):
        for val in self._gen(*self._args, **self._kwargs):
            if self._should_terminate():
                break
            else:
                self._accum.append(val)

    def join(self, *args):
        threading.Thread.join(self, *args)
        return self._accum

def producer(seed):
    random.seed(seed)

    while True:
        sleep(1)
        yield random.randint(0,100)
        
def collect(id):
    vals = []
    for val in producer(id):
        vals.append(val)
        print(f"From {id}: {val}")
    return vals

def futures():
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [ executor.submit(collect, i) for i in range(0, 3) ]
        sleep(10)
        results = [ future.result() for future in futures ]

def stop_thread(t: AccumulatorThread):
    t._queue.put(None)

def main():
    q = queue.Queue()
    t = AccumulatorThread(queue=q, gen=producer, args=(0,))
    t.start()
    sleep(5)
    stop_thread(t)
    # AccumulatorThread.terminate = True
    res = t.join()
    print(res)

if __name__ == "__main__":
    main()


