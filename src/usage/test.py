from time import sleep
from process_test import ProcessTester
from container_test import ContainerTester
from usage.metrics import process_metrics_generator
from container_usage import container_metrics_generator
from multithreading import sample
from lib import MetricsSample

# takes a list of lists of generator results and merges the
# inner lists component-wise based on the time sampled
# i.e., [res[0][0] + res[1][0] + ..., res[0][1] + res[1][1] + ..., ...]
def merge_metrics(results):
    def transpose(ls):
        minlen = min([len(l) for l in ls])
        return [[l[i] for l in ls] for i in range(0, minlen)]

    return [ MetricsSample.merge_many(t) for t in transpose(results) ]

def test():
    proc_tester = ProcessTester()
    container_tester = ContainerTester()

    procs = proc_tester.spawn(3)
    containers = container_tester.spawn(3)

    proc_gens = [ process_metrics_generator(proc) for proc in procs ]
    container_gens = [ container_metrics_generator(c) for c in containers ]
    gens = proc_gens + container_gens

    results = sample(gens, delay=2, duration=10)

    print(merge_metrics(results))

def main():
    test()

if __name__ == "__main__":
    main()
