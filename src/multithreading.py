import threading
import queue
import random
from time import sleep
import logging

logger = logging.getLogger("accum_thread")

# takes a generator function (with __next__() method)
# produces a thread object that continuously generates & stores values until...
# global/local terminate signal is set OR generator runs out of values
class AccumulatorThread(threading.Thread):
    # static termination stuff
    terminate = False

    def __init__(self, queue=queue.Queue(), delay=0, gen=None):
        if gen is None:
            raise ValueError("Must provide 'gen' argument")
        threading.Thread.__init__(self)
        self._accum = [] # used to collect sampled values
        self._queue = queue # used to send stop signal to thread
        self._delay = delay # the time to sleep before re-sampling
        self._gen = gen # generator function/class that yields values
        self.err = False
    
    def _should_terminate(self):
        flag = (self._queue.get() is None) if not self._queue.empty() else False
        return AccumulatorThread.terminate or flag

    def run(self):
        while True:
            if self._should_terminate():
                break
            else:
                try:
                    val = next(self._gen)
                    self._accum.append(val)
                except:
                    logger.warn("Generator stopped producing values")
                    self.err = True
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
        

def stop_thread(t: AccumulatorThread):
    t._queue.put(None)

def stop_all_threads():
    AccumulatorThread.terminate = True

# generators: a list of generators that produce MetricsSample objects
# delay: time to wait between each sampling
# duration: total time to sample
# returns a list of results from each generator
def sample(generators, delay, duration):
    threads = [
        AccumulatorThread(gen=gen, delay=delay)
        for gen in generators
    ]

    for t in threads:
        t.start()

    sleep(duration)
    stop_all_threads()
    return [ t.join() for t in threads ]

def main():
    # q = queue.Queue()
    t = AccumulatorThread(gen=producer(0), delay=2)
    t.start()
    sleep(10)
    stop_thread(t)
    # AccumulatorThread.terminate = True
    res = t.join()
    print(res)

if __name__ == "__main__":
    main()


