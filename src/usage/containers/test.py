import docker

def idx_name(i):
    return f"test-{i}"

def spawn_containers(client, n):
    return [
        client.containers.run('alpine', '/bin/sh', name=idx_name(i), detach=True, auto_remove=True, tty=True)
        for i in range(0, n)
    ]

def running_containers(containers_list):
    return list(filter(lambda c: c.status == 'running', containers_list))

def main():

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
        

if __name__ == "__main__":
    main()
