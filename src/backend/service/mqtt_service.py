import structlog
from src.backend.mqtt import EMGMQTTClient


class MQTTService:
    def __init__(self):
        self.mqtt_client = None
        self.logger = structlog.get_logger(__name__)
        self.mqtt_client

    def setup_mqtt_client(self, broker_host="localhost", broker_port=8083, username=None, password=None,
                          topic_pattern="emg/+/data", transport="websockets", client_id="default",
                          message_handler=None):
        try:
            self.mqtt_client = EMGMQTTClient(
                broker_host,
                broker_port,
                message_handler,
                username,
                password,
                topic_pattern,
                transport,
                client_id
            )
            self.mqtt_client.connect()
            self.logger.info(
                "MQTT client successfully connected to broker"
            )
        except Exception:
            raise

    def disconnect_client(self, client_id="default"):
        topic = "control/disconnect"
        payload = {"client_id": client_id}
        self.mqtt_client.publish(topic, payload)
        self.logger.info(
            "MQTT client successfully disconnected",
            mqtt_client_id=client_id
        )
