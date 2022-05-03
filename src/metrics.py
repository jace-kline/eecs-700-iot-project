from re import L
import psutil
from functools import reduce

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
        # return MetricsSample(
        #     **dict([ (k, v0 + v1) for ((k, v0), v1) 
        #     in zip(self.__dict__.items(), other.__dict__.values())
        #     ])
        # )
        return MetricsSample(
            cpu_percentage=self.cpu_percentage + other.cpu_percentage,
            memory_percentage=self.memory_percentage + other.memory_percentage,
            rx_bytes_delta=self.rx_bytes_delta + other.rx_bytes_delta,
            tx_bytes_delta=self.tx_bytes_delta + other.tx_bytes_delta
        )

    def merge_many(ls):
        return reduce(lambda l, r: l.merge(r), ls)

    def avg(ls):
        accum = MetricsSample.merge_many(ls)
        l = len(ls)
        return MetricsSample(
            cpu_percentage=accum.cpu_percentage / l,
            memory_percentage=accum.memory_percentage / l,
            rx_bytes_delta=accum.rx_bytes_delta / l,
            tx_bytes_delta=accum.tx_bytes_delta / l,
        )

    def max(ls):
        return MetricsSample(
            cpu_percentage=max([ s.cpu_percentage for s in ls ]),
            memory_percentage=max([ s.memory_percentage for s in ls ]),
            rx_bytes_delta=max([ s.rx_bytes_delta for s in ls ]),
            tx_bytes_delta=max([ s.tx_bytes_delta for s in ls ])
        )

    def to_csv_str(self):
        s = ""
        metrics = [ self.cpu_percentage, self.memory_percentage, self.rx_bytes_delta, self.tx_bytes_delta ]
        i = 0
        for metric in metrics:
            s += f"{metric}"
            if i < len(metrics) - 1:
                s += ","
            i += 1

        return s

# takes a list of lists of generator results and merges the
# inner lists component-wise based on the time sampled
# i.e., [res[0][0] + res[1][0] + ..., res[0][1] + res[1][1] + ..., ...]
def merge_metrics(results):
    def transpose(ls):
        minlen = min([len(l) for l in ls])
        return [[l[i] for l in ls] for i in range(0, minlen)]

    return [ MetricsSample.merge_many(t) for t in transpose(results) ]

def process_cpu_percentage(proc):
    # uses last queried CPU stats as the 'delta' since interval=None
    # returns 0 on first time queried
    return proc.cpu_percent(interval=None) / psutil.cpu_count()

def process_memory_percentage(proc):
    return proc.memory_percent()

def process_rx_bytes(proc):
    return proc.io_counters().read_chars

def process_tx_bytes(proc):
    return proc.io_counters().write_chars

def process_metrics_generator(proc):
    rx_bytes = process_rx_bytes(proc)
    tx_bytes = process_tx_bytes(proc)

    while True:
        # rx
        rx_bytes_delta = process_rx_bytes(proc) - rx_bytes
        rx_bytes = rx_bytes + rx_bytes_delta

        # tx
        tx_bytes_delta = process_tx_bytes(proc) - tx_bytes
        tx_bytes = tx_bytes + tx_bytes_delta
        yield MetricsSample(**{
            'cpu_percentage': process_cpu_percentage(proc),
            'memory_percentage': process_memory_percentage(proc),
            'rx_bytes_delta': rx_bytes_delta,
            'tx_bytes_delta': tx_bytes_delta
        })

def container_stats_cpu_percentage(stats):
    usage_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
    system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
    num_cpus = stats['cpu_stats']['online_cpus']
    
    percentage = (usage_delta / system_delta) * num_cpus * 100
    return percentage

def container_stats_memory_percentage(stats):
    return 100 * (stats['memory_stats']['usage'] / stats['memory_stats']['limit'])

def container_stats_network_rx_bytes(stats):
    return sum([ network['rx_bytes'] for network in stats['networks'].values() ])

def container_stats_network_tx_bytes(stats):
    return sum([ network['tx_bytes'] for network in stats['networks'].values() ])

def container_cpu_percentage_static(container):
    stats = container.stats(stream=False)
    return container_stats_cpu_percentage(stats)

def container_metrics_generator(container):
    first_read = True
    rx_bytes = 0
    tx_bytes = 0
    for stats in container.stats(stream=True, decode=True):
        if first_read:
            first_read = False
            rx_bytes = container_stats_network_rx_bytes(stats)
            tx_bytes = container_stats_network_tx_bytes(stats)
            continue
        # rx
        rx_bytes_delta = container_stats_network_rx_bytes(stats) - rx_bytes
        rx_bytes = rx_bytes + rx_bytes_delta

        # tx
        tx_bytes_delta = container_stats_network_tx_bytes(stats) - tx_bytes
        tx_bytes = tx_bytes + tx_bytes_delta
        yield MetricsSample(**{
            'cpu_percentage': container_stats_cpu_percentage(stats),
            'memory_percentage': container_stats_memory_percentage(stats),
            'rx_bytes_delta': rx_bytes_delta,
            'tx_bytes_delta': tx_bytes_delta
        })