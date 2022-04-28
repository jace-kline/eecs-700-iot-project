import sys
from lib import create_mqtt_client, load_mqtt_config_yaml
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
        logger.info(f"Received randnum {data['randnum']}")
        # save data to DB

        # respond to ACK_TOPIC
        payload = json.dumps({ 'ack' : data['randnum'] })
        client.publish(ACK_TOPIC, payload)
        logger.info(f"Published ACK to {ACK_TOPIC}")

def run_script():
    # read in client name as argument
    config_yml_path = sys.argv[1] if len(sys.argv) > 1 else None

    if config_yml_path is None:
        print("Supply MQTT client config YAML file as argument to this script")
        exit(1)
    
    config = load_mqtt_config_yaml(config_yml_path)

    # create Paho MQTT client from YAML config file
    client = create_mqtt_client(config, "custom_middleware")

    # set callback function for receiving messages
    client.on_message = on_message

    for topic in SUBSCRIPTIONS:
        client.subscribe(topic)
        logger.info(f"Subscribed to {topic}")

    # listen for updates
    client.loop_forever()

# if this script is executed directly (not imported), then run main()
if __name__ == "__main__":
    run_script()