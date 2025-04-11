from typing import Dict
import structlog
from src.backend.abstraction import MQTTAbstraction
from src.backend.mqtt import EMGMQTTClient


class MQTTService:
    def __init__(self):
        self.logger = structlog.get_logger(__name__)

    def setup_mqtt_client(self, broker_host="localhost", broker_port=8083, username=None, password=None,
                          topic_pattern="emg/+/data", transport="websockets", client_id="default",
                          message_handler=None):
        try:
            mqtt_client = EMGMQTTClient(
                broker_host,
                broker_port,
                message_handler,
                username,
                password,
                topic_pattern,
                transport,
                client_id
            )
            mqtt_client.connect()
            self.logger.info(
                "MQTT client successfully connected to broker"
            )
        except Exception:
            raise


