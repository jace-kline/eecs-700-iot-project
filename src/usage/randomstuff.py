from lib import MetricsSample

def testmerge():

    samples = [ MetricsSample(**{
            'cpu_percentage': 3.0,
            'memory_percentage': 5.0,
            'rx_bytes_delta': 30,
            'tx_bytes_delta': 50
        }) for _ in range(0, 10)
    ]

    merge = MetricsSample.merge_many(samples)
    
    print(merge)

def transpose(ls):
    minlen = min([len(l) for l in ls])
    return [[l[i] for l in ls] for i in range(0, minlen)]

def main():
    iters = [[1,2,3] for _ in range(0,3)]
    print(transpose(iters))

if __name__ == "__main__":
    main()
