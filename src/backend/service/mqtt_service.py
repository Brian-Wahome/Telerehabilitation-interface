import structlog
from src.backend.mqtt import EMGMQTTClient
from ..exceptions import MQTTClientNotFound


class MQTTService:
    def __init__(self):
        self.mqtt_clients = {}
        self.logger = structlog.get_logger(__name__)
        self.mqtt_client

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
            self.mqtt_clients[client_id] = mqtt_client
            self.logger.info(
                "MQTT client successfully connected to broker",
                mqtt_client_id=client_id
            )
        except Exception as e:
            self.logger.error(
                "Failed to setup MQTT client",
                mqtt_client_id=client_id,
                error=str(e)
            )
            raise

    def disconnect_client(self, client_id="default"):
        try:
            # Check if we have this specific client ID
            if client_id not in self.mqtt_clients:
                self.logger.error(
                    f"MQTT client with ID '{client_id}' not found",
                    mqtt_client_id=client_id,
                )
                raise MQTTClientNotFound(f"MQTT client with ID '{client_id}' not found")

            # Get the client we want to disconnect
            client = self.mqtt_clients[client_id]

            # Send disconnect command using the client itself
            topic = "control/disconnect"
            payload = {"client_id": client_id}
            client.publish(topic, payload)

            self.logger.info(
                "Disconnect command sent to client",
                mqtt_client_id=client_id
            )
            return True

        except Exception as e:
            self.logger.error(
                "Error disconnecting client",
                mqtt_client_id=client_id,
                error=str(e)
            )
            raise
