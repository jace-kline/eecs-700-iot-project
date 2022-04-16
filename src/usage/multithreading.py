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

    def __init__(self, queue=queue.Queue(), delay=0, gen=None, args=(), kwargs={}):
        if gen is None:
            raise ValueError("Must provide 'gen' argument")
        threading.Thread.__init__(self)
        self._accum = [] # used to collect sampled values
        self._queue = queue # used to send stop signal to thread
        self._delay = delay # the time to sleep before re-sampling
        self._gen = gen # generator function/class that yields values
        self._args = args # arguments to the generator
        self._kwargs = kwargs # keyword arguments to the generator
    
    def _should_terminate(self):
        flag = (self._queue.get() is None) if not self._queue.empty() else False
        return AccumulatorThread.terminate or flag

    def run(self):
        gen = self._gen(*self._args, **self._kwargs)

        while True:
            if self._should_terminate():
                break
            else:
                try:
                    val = next(gen)
                    self._accum.append(val)
                except StopIteration:
                    break
                if self._delay > 0:
                    sleep(self._delay)


    def join(self, *args):
        threading.Thread.join(self, *args)
        return self._accum

def producer(seed):
    random.seed(seed)

    while True:
        yield random.randint(0,100)
        
# def collect(id):
#     vals = []
#     for val in producer(id):
#         vals.append(val)
#         print(f"From {id}: {val}")
#     return vals

# def futures():
#     with concurrent.futures.ThreadPoolExecutor() as executor:
#         futures = [ executor.submit(collect, i) for i in range(0, 3) ]
#         sleep(10)
#         results = [ future.result() for future in futures ]

def stop_thread(t: AccumulatorThread):
    t._queue.put(None)

def stop_all_threads():
    AccumulatorThread.terminate = True

def main():
    # q = queue.Queue()
    t = AccumulatorThread(gen=producer, args=(0,), delay=2)
    t.start()
    sleep(10)
    stop_thread(t)
    # AccumulatorThread.terminate = True
    res = t.join()
    print(res)

if __name__ == "__main__":
    main()


