from time import sleep
import psutil

def process_cpu_percentage(proc, interval):
    return proc.cpu_percent(interval=interval) / psutil.cpu_count()

def process_memory_percentage(proc):
    return proc.memory_percent()

def process_rx_bytes(proc):
    return proc.io_counters().read_chars

def process_tx_bytes(proc):
    return proc.io_counters().write_chars

def process_metrics_generator(proc, delay):
    rx_bytes = process_rx_bytes(proc)
    tx_bytes = process_tx_bytes(proc)

    while True:
        # rx
        rx_bytes_delta = process_rx_bytes(proc) - rx_bytes
        rx_bytes = rx_bytes + rx_bytes_delta

        # tx
        tx_bytes_delta = process_tx_bytes(proc) - tx_bytes
        tx_bytes = tx_bytes + tx_bytes_delta
        yield {
            'cpu_percentage': process_cpu_percentage(proc, delay),
            'memory_percentage': process_memory_percentage(proc),
            'rx_bytes_delta': rx_bytes_delta,
            'tx_bytes_delta': tx_bytes_delta
        }

def test1():
    procs = list(filter(lambda p: p.name() == "nc", psutil.process_iter()))
    print(procs[0].children(recursive=True))
    for proc in procs:
        print(proc.cpu_percent(interval=0.5))
        print(proc.memory_percent())
        print(proc.io_counters().read_chars)
        print(proc.io_counters().write_chars)

def test_generator():
    procs = list(filter(lambda p: p.name() == "nc", psutil.process_iter()))
    proc = procs[0]
    for metrics in process_metrics_generator(proc, delay=1.0):
        print(metrics)

def network():
    procs = list(filter(lambda p: p.name() == "nc", psutil.process_iter()))
    proc = procs[0]
    for _ in range(0, 10):
        print(proc.io_counters())
        sleep(2)


def main():
    test_generator()

if __name__ == "__main__":
    main()