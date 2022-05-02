import sys
import os
from lib import MqttConfig, RedisConfig, create_mqtt_client, create_redis_client, load_mqtt_config_yaml, load_redis_config_yaml
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("middleware")

DATA_TOPIC = "device/randnum_device/data"
SUBSCRIPTIONS = [ DATA_TOPIC ]

ACK_TOPIC = "device/randnum_device/ack"

def on_message(client, data, message):
    logger.info(f"Received message from topic '{message.topic}': {message.payload.decode()}")
    if message.topic == DATA_TOPIC:
        # extract randnum from message
        data = json.loads(message.payload.decode())
        randnum = data['randnum']
        logger.info(f"Received randnum {randnum}")

        # save data to DB, then get the value back
        client.redis_.set('randnum', randnum)
        val = int(client.redis_.get('randnum').decode())
        logger.info("Wrote and retrieved randnum from DB")

        # respond to ACK_TOPIC
        payload = json.dumps({ 'ack' : val })
        client.publish(ACK_TOPIC, payload)
        logger.info(f"Published ACK to {ACK_TOPIC}")

def run(mqtt_config, redis_config):
    # create Paho MQTT client from YAML config file
    client = create_mqtt_client(mqtt_config, "custom_middleware")
    redis_ = create_redis_client(redis_config)

    # store the redis instance in the client object
    client.redis_ = redis_

    # set callback function for receiving messages
    client.on_message = on_message

    for topic in SUBSCRIPTIONS:
        client.subscribe(topic)
        logger.info(f"Subscribed to {topic}")

    # listen for updates
    client.loop_forever()

# when in container, read config as env variables
# same key names as YAML config
def run_container():

    mqtt_config = MqttConfig(
        broker_ip=os.getenv('mqtt_host', 'localhost'),
        port=int(os.getenv('mqtt_port', 1883)),
        tls_enabled=bool(os.getenv('mqtt_tls_enabled', False)),
        websockets=bool(os.getenv('mqtt_websockets', False)),
        cafile=os.getenv('cafile', None),
        certfile=os.getenv('certfile', None),
        keyfile=os.getenv('keyfile', None)
    )

    redis_config = RedisConfig(
        host=os.getenv('redis_host', 'localhost'),
        port=os.getenv('redis_port', 6379),
        db=os.getenv('redis_db', 0)
    )

    run(mqtt_config, redis_config)

# when local, provide YAML file path as argument
def run_local():
    # read in client name as argument
    mqtt_config_yml_path = sys.argv[2] if len(sys.argv) > 2 else None

    redis_config_yml_path = sys.argv[3] if len(sys.argv) > 3 else None

    if mqtt_config_yml_path is None or redis_config_yml_path is None:
        print("Supply (MQTT YAML, Redis YAML) client config paths as arguments to this script")
        exit(1)
    
    mqtt_config = load_mqtt_config_yaml(mqtt_config_yml_path)
    redis_config = load_redis_config_yaml(redis_config_yml_path)

    run(mqtt_config, redis_config)

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else None

    if mode == "--local": run_local()
    elif mode == "--container": run_container()
    else: print("Must supply '--local' or '--container' as first argument")

# if this script is executed directly (not imported), then run main()
if __name__ == "__main__":
    main()