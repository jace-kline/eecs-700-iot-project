from client import run_client
from lib import RedisConfig, create_mqtt_client, MqttConfig, load_mqtt_config_yaml, load_redis_config_yaml
from runner import CmdLauncher, ScenarioRunner, log_results
from time import sleep
import logging

logger = logging.getLogger("scenario")
logger.setLevel(logging.INFO)

# REDISCONFIG = RedisConfig(
#     host='localhost',
#     port=6379,
#     db=0
# )

class LocalRedisLauncher(CmdLauncher):
    def __init__(self, config, redis_config_path=None):
        self.config = config
        cmd = "redis-server"
        super().__init__(cmd)

    def wait(self):
        logger.info("Waiting for Redis DB to startup")
        sleep(2)
        return True

class LocalBrokerLauncher(CmdLauncher):
    def __init__(self, config, broker_config_path=None):
        self.config = config
        cmd = f"mosquitto -d -p {config.port}"
        if broker_config_path is not None:
            cmd += f" -c {broker_config_path}"
        super().__init__(cmd)

    def wait(self):
        while True:
            try:
                client = create_mqtt_client(self.config, "test")
                return True
            except:
                pass

class LocalMiddlewareLauncher(CmdLauncher):
    def __init__(self, mqtt_config_path, redis_config_path):
        cmd = f"python3 middleware.py --local {mqtt_config_path} {redis_config_path}"
        super().__init__(cmd)

    def wait(self):
        sleep(2)
        return True

def run_notls():
    mqtt_config_path = "config/client/config-custom-notls.yml"
    redis_config_path = "config/client/config-redis-notls.yml"
    broker_config_path = "config/mosquitto/mosquitto.notls.conf"

    metrics, rtts = run(mqtt_config_path, redis_config_path, broker_config_path)

    log_results(
        scenario="Custom Middleware",
        containerized=False,
        tls=False,
        rtts=rtts,
        metrics=metrics,
        dryrun=False
    )

def run_tls():
    mqtt_config_path = "config/client/config-custom-tls.yml"
    redis_config_path = "config/client/config-redis-notls.yml"
    broker_config_path = "config/mosquitto/mosquitto.tls.conf"

    metrics, rtts = run(mqtt_config_path, redis_config_path, broker_config_path)

    log_results(
        scenario="Custom Middleware",
        containerized=False,
        tls=True,
        rtts=rtts,
        metrics=metrics,
        dryrun=False
    )

def run(mqtt_config_path, redis_config_path, broker_config_path):
    MQTTCONFIG = load_mqtt_config_yaml(mqtt_config_path)
    REDISCONFIG = load_redis_config_yaml(redis_config_path)
    
    broker_launcher = LocalBrokerLauncher(MQTTCONFIG, broker_config_path=broker_config_path)
    redis_launcher = LocalRedisLauncher(REDISCONFIG)
    middleware_launcher = LocalMiddlewareLauncher(mqtt_config_path, redis_config_path)

    client_func = lambda: run_client(MQTTCONFIG, iterations=20)
    launchers = [ redis_launcher, broker_launcher, middleware_launcher ]
    runner = ScenarioRunner(
        client_func,
        launchers=launchers,
        ps_names=["mosquitto", "redis-server"],
        track_containers=False,
        clean_containers=False
    )

    metrics, rtts = runner.run()
    runner.cleanup()

    return metrics, rtts

    # print(metrics)
    # print(rtts)


if __name__ == "__main__":
    run_tls()
