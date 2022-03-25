import psutil

def test1():
    procs = list(filter(lambda p: p.name() == "docker", psutil.process_iter()))
    print(procs[1].children(recursive=True))
    for proc in procs:
        print(proc.cpu_percent(interval=0.5))