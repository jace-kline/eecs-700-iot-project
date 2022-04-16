from time import sleep
from process_test import ProcessTester
from container_test import ContainerTester
from process_usage import process_metrics_generator
from container_usage import container_metrics_generator
from multithreading import AccumulatorThread, stop_all_threads
from functools import reduce
from lib import MetricsSample

# each group represents a generator(obj)
# and a list of objects to sample the generator over
# e.g., "processes" and "containers" could be 2 groups
class SamplerGroup(object):
    def __init__(self, name=None, gen=None, objs=[]):
        self.name = name
        self.gen = gen
        self.objs = objs

class Sampler(object):
    def __init__(self, sampler_groups):
        self.groups = sampler_groups
        self.results = []

    # delay = time to wait between each sampling
    # duration = total time to sample
    def run(self, delay, duration):
        # create a list of lists
        # each inner list holds the threads of a sampled group
        grouped_threads = [
                [ 
                    AccumulatorThread(gen=group.gen, args=(obj,), delay=delay)
                    for obj in group.objs
                ] for group in self.groups
            ]

        def flatten(ls):
            return reduce(lambda l, r: l + r, ls)

        for t in flatten(grouped_threads):
            t.start()

        sleep(duration)
        stop_all_threads()
        self.results = [[ t.join() for t in group_threads ] for group_threads in grouped_threads]
        return self.results


def test():
    proc_tester = ProcessTester()
    container_tester = ContainerTester()

    procs = proc_tester.spawn(3)
    containers = container_tester.spawn(3)

    proc_group = SamplerGroup(
        name="processes",
        gen=process_metrics_generator,
        objs=procs
    )

    container_group = SamplerGroup(
        name="containers",
        gen=container_metrics_generator,
        objs=containers
    )

    groups = [proc_group, container_group]

    sampler = Sampler(groups)
    results = sampler.run(delay=2, duration=10)

    # results = [ [ [], [], ... ] , [ [], [], ... ], ... ]
    # results[i] = group results (by obj)
    # results[i][j] = obj metrics samples over time
    # results[i][j][k] = MetricsSample instance

    def transpose(ls):
        minlen = min([len(l) for l in ls])
        return [[l[i] for l in ls] for i in range(0, minlen)]

    # merge metrics based on the time sampled (component-wise)
    intra_group_merge_metrics = [
        [ MetricsSample.merge_many(component) for component in transposed ]
        for transposed in [ transpose(group) for group in results ]
    ]

    print(intra_group_merge_metrics)

def main():
    test()

if __name__ == "__main__":
    main()
