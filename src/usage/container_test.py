from time import sleep
import docker
import json
from container_usage import container_metrics_generator
from multithreading import AccumulatorThread, stop_thread, stop_all_threads

def idx_name(i):
    return f"test-{i}"

def spawn_containers(client, n):
    return [
        client.containers.run('alpine', '/bin/sh', name=idx_name(i), detach=True, tty=True)
        for i in range(0, n)
    ]

def running_containers(containers_list):
    return list(filter(lambda c: c.status == 'running', containers_list))

def test_threaded_stats_single_container():
    client = docker.from_env()
    spawned = spawn_containers(client, 1)
    container = client.containers.list()[0]
    t = AccumulatorThread(gen=container_metrics_generator, args=(container,))
    t.start()
    sleep(5)
    stop_thread(t)
    res = t.join()
    print(res)
    for c in spawned:
        c.stop()
        c.remove()
    client.close()

def test_threaded_stats_multi_container():
    client = docker.from_env()
    spawned = spawn_containers(client, 3)
    threads = [ 
        AccumulatorThread(gen=container_metrics_generator, args=(container,))
        for container in client.containers.list()
    ]
    for t in threads:
        t.start()
    sleep(5)
    stop_all_threads()
    results = [ t.join() for t in threads ]
    print(results)
    for c in spawned:
        c.stop()
        c.remove()
    client.close()



def get_container_stats():
    client = docker.from_env()
    spawned = spawn_containers(client, 1)
    container = client.containers.list()[0]
    stats = container.stats(stream=False)
    print(stats)
    # print(tx_bytes(stats))
    for c in spawned:
        c.stop()
        c.remove()
    client.close()

def test_print_running():
    client = docker.from_env()
    # spawn some containers
    spawned = spawn_containers(client, 5)
    print(spawned)

    # pause a container, exit a container
    spawned[1].pause()
    spawned[3].stop()

    # get only the 'running' containers
    running = running_containers(client.containers.list())
    print(running)

    client.close()

def main():
    test_threaded_stats_multi_container()

if __name__ == "__main__":
    main()
