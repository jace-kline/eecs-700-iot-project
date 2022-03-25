import docker
import json

def container_stats_cpu_percentage(stats):
    usage_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
    system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
    num_cpus = stats['cpu_stats']['online_cpus']
    
    percentage = (usage_delta / system_delta) * num_cpus * 100
    return percentage

def container_stats_memory_percentage(stats):
    return 100 * (stats['memory_stats']['usage'] / stats['memory_stats']['limit'])

def container_stats_network_rx_packets(stats):
    return stats['networks']['eth0']['rx_packets']

def container_stats_network_tx_packets(stats):
    return stats['networks']['eth0']['tx_packets']

def container_cpu_percentage_static(container):
    stats = container.stats(stream=False)
    return container_stats_cpu_percentage(stats)

def container_metrics_generator(container):
    first_read = True
    for stats in container.stats(stream=True, decode=True):
        if first_read:
            first_read = False
            continue
        yield {
            'cpu_percentage': container_stats_cpu_percentage(stats),
            'memory_percentage': container_stats_memory_percentage(stats),
            'rx_packets': container_stats_network_rx_packets(stats),
            'tx_packets': container_stats_network_tx_packets(stats)
        }

def dockerstats():
    client = docker.from_env()
    containers = client.containers.list()
    container = containers[0]
    # print_stats_stream(container)
    for metrics in container_metrics_generator(container):
        print(metrics)

def print_stats_stream(container):
    for stats in container.stats(stream=True, decode=True):
        print(json.dumps(stats, indent=4))

if __name__ == "__main__":
    dockerstats()
    # test()