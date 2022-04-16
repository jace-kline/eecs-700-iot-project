from time import sleep
import subprocess
import sys
import socket
import os
import threading

NC_PORT = 1234

def spawn_clones(n):
    for _ in range(0, n):
        subprocess.Popen(["python3", "busy.py", "0"])

def spawn_netcat_listener(port):
    subprocess.Popen(["nc", "-nlvp", f"{port}"])

def create_children():
    # if we are the root busy.py instance, create a netcat listener
    # '--root' must be second argument
    if len(sys.argv) > 2 and sys.argv[2] == "--root":
        spawn_netcat_listener(NC_PORT)
    
    # the first argument specifies how many children clones to spawn
    if len(sys.argv) > 1:
        n = int(sys.argv[1])
        spawn_clones(n)

def busy_network(delay):
    PID = os.getpid()
    HOST = 'localhost'

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        # Connect to server and send data
        sock.connect((HOST, NC_PORT))
        data = f"From {PID}"

        while True:
            sock.sendall(bytes(data + "\n", "utf-8"))
            sleep(delay)
            # Receive data from the server and shut down
            # received = str(sock.recv(1024), "utf-8")

def busy_cpu():
    val = 0
    while True:
        val = val + 1

def main():
    # create children processes
    create_children()
    
    # do some stuff
    t0 = threading.Thread(target=busy_network, args=(0.5,))
    t1 = threading.Thread(target=busy_cpu)
    threads = [t0, t1]
    for t in threads:
        t.start()

if __name__ == "__main__":
    main()