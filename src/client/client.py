from lib import create_mqtt_client, Device, Timer
import sys
import time
import json

timer = Timer()

# when publishing, start a timer
def on_publish(client, userdata, mid):
    timer.start()

# when receiving, stop timer and record duration
def on_message(client, userdata, message):
    if message.topic == f'device/{client.name}/data':
        dur = timer.stop()
        print(dur)

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
    client.on_publish = on_publish

    # set callback function for receiving messages
    client.on_message = on_message

    # start new thread to listen to incoming events
    client.loop_start()

    # instantiate device that produces data
    device = Device()

    iterations = 24 # number of loops
    interval = 5 # seconds

    # publish new data in a loop
    for _ in range(0, iterations):
        # read device data
        value = device.read()

        # publish the data
        topic = f'device/{client.name}/data'
        payload = json.dumps({ 'value': value })
        client.publish(topic, payload)

        # wait before looping again
        time.sleep(interval)

    # save the results of the publish->receive durations to a file
    # durs = client.timer.durations()
    # for dur in durs:
    #     print(dur)

# if this script is executed directly (not imported), then run main()
if __name__ == "__main__":
    main()
