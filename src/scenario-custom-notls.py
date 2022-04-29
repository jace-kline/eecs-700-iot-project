from client import run_client
from lib import create_mqtt_client, MqttConfig
from runner import CmdLauncher, ScenarioRunner
from metrics import merge_metrics
from time import sleep

MQTTCONFIG = MqttConfig(
    broker_ip='localhost',
    port=1883,
    tls_enabled=False,
    cafile=None,
    certfile=None,
    keyfile=None
)

def broker_wait_thunk(config):
    def broker_wait():
        while True:
            try:
                client = create_mqtt_client(config, "test")
                return True
            except:
                pass

    return broker_wait

# launch Mosquitto broker
# return a list of Process objects that are spawned
def mk_broker_launcher(config, broker_config_path=None):

    cmd = f"mosquitto -d -p {config.port}"
    if broker_config_path is not None:
        cmd += f" -c {broker_config_path}"

    return CmdLauncher(
        cmd=cmd,
        wait=broker_wait_thunk(config)
    )

def mk_middleware_launcher(config):
    cmd = "python3 middleware.py configs/config-custom-notls.yml"
    
    def wait():
        sleep(2)
        return True

    return CmdLauncher(
        cmd=cmd,
        wait=wait
    )


def run():
    broker_launcher = mk_broker_launcher(MQTTCONFIG)
    middleware_launcher = mk_middleware_launcher(MQTTCONFIG)
    client_func = lambda: run_client(MQTTCONFIG, iterations=5)
    launchers = [ broker_launcher, middleware_launcher ]
    runner = ScenarioRunner(
        client_func,
        launchers=launchers,
        ps_names=["mosquitto"],
        track_containers=False,
        clean_containers=False
    )

    metrics, rtts = runner.run()
    runner.cleanup()

    print(rtts)
    print(merge_metrics(metrics))


if __name__ == "__main__":
    run()
