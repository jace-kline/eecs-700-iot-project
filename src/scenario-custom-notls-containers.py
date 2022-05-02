from client import run_client
from lib import MqttConfig
from runner import CmdLauncher, ScenarioRunner, launch_cmd
from metrics import merge_metrics
from time import sleep
import logging

logger = logging.getLogger("scenario")
logger.setLevel(logging.INFO)

MQTTCONFIG = MqttConfig(
    broker_ip='localhost',
    port=1883,
    tls_enabled=False,
    websockets=False,
    cafile=None,
    certfile=None,
    keyfile=None
)

class DockerComposeLauncher(CmdLauncher):
    def __init__(self, compose_file_path):
        self.compose_file_path = compose_file_path
        cmd = f'docker-compose -f {self.compose_file_path} up -d'
        super().__init__(cmd)
    
    def wait(self):
        logger.info("Waiting 10s for docker compose")
        sleep(10)
        return True

    def clean(self):
        logger.info("Cleaning docker compose deployment")
        cmd = f'docker-compose -f {self.compose_file_path} down'
        popen = launch_cmd(cmd)
        popen.wait()

def run():
    
    compose_file_path = 'custom-middleware-docker/notls.compose.yml'
    compose_launcher = DockerComposeLauncher(compose_file_path)

    client_func = lambda: run_client(MQTTCONFIG, iterations=5)
    launchers = [ compose_launcher ]
    runner = ScenarioRunner(
        client_func,
        launchers=launchers,
        track_containers=True,
        clean_containers=True
    )

    metrics, rtts = runner.run()
    runner.cleanup()

    print(rtts)
    print(merge_metrics(metrics))


if __name__ == "__main__":
    run()
