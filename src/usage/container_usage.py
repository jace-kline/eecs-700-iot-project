from lib import MetricsSample

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
