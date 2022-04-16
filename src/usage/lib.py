from functools import reduce
from timeit import default_timer as timer

class MetricsSample(object):
    def __init__(
        self,
        cpu_percentage=None,
        memory_percentage=None,
        rx_bytes_delta=None,
        tx_bytes_delta=None
    ):
        self.cpu_percentage = cpu_percentage
        self.memory_percentage = memory_percentage
        self.rx_bytes_delta = rx_bytes_delta
        self.tx_bytes_delta = tx_bytes_delta

    def __str__(self) -> str:
        return f"MetricsSample({self.__dict__.__str__()})"

    def __repr__(self) -> str:
        return self.__str__()

    # component-wise merge of 2 MetricsSample objects
    def merge(self, other):
        return MetricsSample(
            **dict([ (k, v0 + v1) for ((k, v0), v1) 
            in zip(self.__dict__.items(), other.__dict__.values())
            ])
        )

    def merge_many(ls):
        return reduce(lambda l, r: l.merge(r), ls)

class Timer:
    def __init__(self):
        self.begin = None
        self.end = None
        self.times = []

    def reset(self):
        self.begin = None
        self.end = None

    def start(self):
        self.begin = timer()

    def stop(self):
        self.end = timer()
        if self.begin is None:
            self.reset()
            raise RuntimeError("Timer never started with start() method")
        else:
            dur = self.end - self.begin
            self.times.append(dur)
            self.reset()
            return dur

    def last(self):
        if len(self.times) == 0:
            raise RuntimeError("No recorded duration values")
        else:
            return self.times[-1]

    def durations(self):
        return self.times