import sys
from lib import create_mqtt_client, Device, Timer
import sys
import time
import json

# enable the timer for each data publish?
ENABLE_TIMER = True

# the MQTT topic the client publishes random values to
DATA_TOPIC = "device/randnum_device/data"

# the MQTT topics the client subscribes to
ACK_TOPIC = "device/randnum_device/ack" # indicates broker received data
SUBSCRIPTIONS = [ ACK_TOPIC ]

def matching_topics(t0, t1):
    l = min(len(t0), len(t1))
    return t0[0:l] == t1[0:l]

# # when publishing, start a timer
# def on_publish(client, userdata, mid):
#     pass

# when receiving, stop timer and record duration
def on_message(client, userdata, message):
    if message.topic == ACK_TOPIC:
        if ENABLE_TIMER:
            dur = client.timer.stop()
            print(f"RTT: {dur}")

def main():
    # read in client name as argument
    config_yml_path = sys.argv[1] if len(sys.argv) > 1 else None

    if config_yml_path is None:
        print("Supply MQTT client config YAML file as argument to this script")
        exit(1)

    # create Paho MQTT client from YAML config file
    client = create_mqtt_client(config_yml_path)

    # # add a timer object to the client so it can be started/stopped when publishing/receiving
    # client.timer = Timer()
    # client.wait_iterations = 3
    client.timer = Timer()

    # set callback function for when message is published
    # client.on_publish = on_publish

    # set callback function for receiving messages
    client.on_message = on_message

    # subscribe to the topic
    for topic in SUBSCRIPTIONS:
        client.subscribe(topic)
        print(f"Subscribed to {topic}")

    # instantiate device that produces random number data
    client.device = Device()

    # ping count
    client.ping = 0

    # start new thread to listen to incoming events
    client.loop_start()

    iterations = 24 # number of loops
    interval = 5 # seconds

    # publish new data in a loop
    # for _ in range(0, iterations):
    while True:
        # read device data
        value = client.device.read()

        # publish the data
        topic = DATA_TOPIC
        payload = json.dumps({ 'randnum' : value })
        client.publish(topic, payload)
        if ENABLE_TIMER:
            client.timer.start()

        # wait before looping again
        time.sleep(interval)

    # save the results of the publish->receive durations to a file
    # durs = client.timer.durations()
    # for dur in durs:
    #     print(dur)

# if this script is executed directly (not imported), then run main()
if __name__ == "__main__":
    main()
