import redis

def main():
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.set('test', 'hello, world')
    print(r.get('test').decode())

if __name__ == "__main__":
    main()