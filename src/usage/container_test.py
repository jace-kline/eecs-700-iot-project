from time import sleep
import docker
import json
from container_usage import container_metrics_generator
from multithreading import AccumulatorThread, stop_thread, stop_all_threads

class ContainerTester(object):
    def __init__(self):
        self.client = docker.from_env()
        self.spawned = []

    def spawn(self, n):
        def idx_name(i):
            return f"test-{i}"

        self.spawned = [
            self.client.containers.run('alpine', '/bin/sh', name=idx_name(i), detach=True, tty=True)
            for i in range(0, n)
        ]

        return self.spawned

    def __del__(self):
        for c in self.spawned:
            c.stop()
            c.remove()
        
        self.client.close()

    def all_containers_list(self):
        return self.client.containers.list()

def running_containers(containers_list):
    return list(filter(lambda c: c.status == 'running', containers_list))

def test_threaded_stats_single_container():
    tester = ContainerTester()
    tester.spawn(1)
    container = tester.all_containers_list()[0]
    t = AccumulatorThread(gen=container_metrics_generator(container), delay=2)
    t.start()
    sleep(10)
    stop_thread(t)
    res = t.join()
    print(res)

def test_threaded_stats_multi_container():
    tester = ContainerTester()
    tester.spawn(3)
    threads = [ 
        AccumulatorThread(gen=container_metrics_generator(container), delay=2)
        for container in tester.all_containers_list()
    ]
    for t in threads:
        t.start()
    sleep(10)
    stop_all_threads()
    results = [ t.join() for t in threads ]
    print(results)
    print(results[0])

def get_container_stats():
    tester = ContainerTester()
    container = tester.all_containers_list()[0]
    stats = container.stats(stream=False)
    print(stats)

def test_print_running():
    tester = ContainerTester()
    # spawn some containers
    spawned = tester.spawn(5)
    print(spawned)

    # pause a container, exit a container
    spawned[1].pause()
    spawned[3].stop()

    # get only the 'running' containers
    running = running_containers(spawned)
    print(running)

def main():
    test_threaded_stats_multi_container()

if __name__ == "__main__":
    main()
