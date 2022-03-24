import yaml
import ssl
import random
from timeit import default_timer as timer
import paho.mqtt.client as paho_client

def load_yaml(path):
    with open(path, 'r') as stream:
        return yaml.load(stream, yaml.Loader)

def create_mqtt_client(config_yml_path):

    def on_connect(client, obj, flags, rc):
        if rc == 0:
            print("MQTT connection successful")
        else:
            print("MQTT connection failed")
            client.disconnect()

    # load config YAML file
    config = load_yaml(config_yml_path)

    # set client params
    client_name = config['client_name']
    client = paho_client.Client(client_name)
    client.name = client_name

    # if TLS enabled, set TLS properties
    if bool(config['tls_enabled']):
        client.tls_set(
            ca_certs=config['cafile'],
            certfile=config['certfile'],
            keyfile=config['keyfile'],
            tls_version=ssl.PROTOCOL_SSLv23
        )
        client.tls_insecure_set(True)
    
    client.on_connect = on_connect

    # attempt to connect to broker
    client.connect(config['broker_ip'], config['port'], 30)

    # subscribe to topics in 'subscriptions' list from config file
    if "subscriptions" in config.keys():
        for topic in config['subscriptions']:
            client.subscribe(topic)
            print(f"Subscribed to {topic}")

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
            dur = self.end - self.begin
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
        
        