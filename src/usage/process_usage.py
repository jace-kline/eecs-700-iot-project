from lib import MetricsSample
import subprocess
import psutil

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
