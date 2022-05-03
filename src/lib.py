from os import name
import ssl
import paho.mqtt.client as paho_client
import random
from timeit import default_timer as timer
import yaml
from collections import namedtuple
import redis

MqttConfig = namedtuple('MqttConfig', [
    'broker_ip', 'port', 'tls_enabled', 'websockets', 'cafile', 'certfile', 'keyfile'
])

RedisConfig = namedtuple('RedisConfig', ['host', 'port', 'db'])

def create_redis_client(redis_conf):
    host = redis_conf.host
    port = redis_conf.port
    db = redis_conf.db
    return redis.Redis(host=host, port=port, db=db)

def load_redis_config_yaml(path):
    conf = load_yaml(path)
    return RedisConfig(**conf)

def load_yaml(path):
    with open(path, 'r') as stream:
        return yaml.load(stream, yaml.Loader)

def load_mqtt_config_yaml(path):
    conf = load_yaml(path)
    if not bool(conf['tls_enabled']):
        conf = { **conf,
            'cafile': None,
            'certfile': None,
            'keyfile': None
        }
    return MqttConfig(**conf)

# Accepts a MqttConfig struct and a client name
# Produces a Paho MQTT Client object
def create_mqtt_client(config, client_name):

    def on_connect(client, obj, flags, rc):
        if rc == 0:
            print("MQTT connection successful")
        else:
            print("MQTT connection failed")
            client.disconnect()

    # create client object
    client = paho_client.Client(client_name)

    # if TLS enabled, set TLS properties
    if bool(config.tls_enabled):
        client.tls_set(
            ca_certs=config.cafile,
            certfile=config.certfile,
            keyfile=config.keyfile,
            tls_version=ssl.PROTOCOL_SSLv23
        )
        client.tls_insecure_set(True)
    
    client.on_connect = on_connect

    # attempt to connect to broker
    client.connect(config.broker_ip, config.port, 30)

    return client

# A mock device that returns random numbers as the "data"
class Device:
    def __init__(self):
        random.seed(1)

    def read(self):
        return random.randint(0,100)

class Timer:
    def __init__(self):
        self.begin = None
        self.end = None
        self.times = []

    def reset(self):
        self.begin = None
        self.end = None

    def start(self):
        self.begin = timer()

    def stop(self):
        self.end = timer()
        if self.begin is None:
            self.reset()
            raise RuntimeError("Timer never started with start() method")
        else:
            dur = (self.end - self.begin) * 1000 # convert s to ms
            self.times.append(dur)
            self.reset()
            return dur

    def last(self):
        if len(self.times) == 0:
            raise RuntimeError("No recorded duration values")
        else:
            return self.times[-1]

    def durations(self):
        return self.times
