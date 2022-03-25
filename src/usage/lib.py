from timeit import default_timer as timer

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