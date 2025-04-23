import uuid

import structlog
from src.backend.mqtt import EMGMQTTClient
from ..exceptions import MQTTClientNotFound


class MQTTService:
    def __init__(self):
        self.mqtt_clients = {}
        self.logger = structlog.get_logger(__name__)

    def setup_mqtt_client(self, broker_host="localhost", broker_port=8083, username=None, password=None,
                          topic_pattern="emg/+/+/data", transport="websockets", client_id=f'emg-client-{uuid.uuid4()}',
                          message_handler=None):
        """
        Function to set up a MQTT client
        :param broker_host: MQTT broker hostname or IP
        :param broker_port: MQTT broker port
        :param username: MQTT broker username (optional)
        :param password: MQTT broker password (optional)
        :param topic_pattern: Topic pattern to subscribe to (default: "emg/+/data")
        :param transport: Transport protocol ("websockets" or "tcp")
        :param client_id: Client identifier
        :param message_handler: Callback function or object method to handle MQTT messages
        :return:
        """
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
        """
        Disconnect client from mqtt broker
        :param client_id: ID of client to be disconnected
        :return:
        """
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

    def remove_client(self, client_id):
        """Remove a client from our registry (after confirming disconnection)"""
        if client_id in self.mqtt_clients:
            del self.mqtt_clients[client_id]
            self.logger.info("Client removed from registry", mqtt_client_id=client_id)
            return True
        return False

    def set_active_exercise_set(self, session_id: str, exercise_set_id: str):
        """Set the active exercise set for a session"""
        self.logger.info(
            "Setting active exercise set",
            session_id=session_id,
            exercise_set_id=exercise_set_id
        )
        return self.mqtt_abstraction.set_active_exercise_set(session_id, exercise_set_id)

    def clear_active_exercise_set(self, session_id: str):
        """Clear the active exercise set for a session"""
        self.logger.info(
            "Clearing active exercise set",
            session_id=session_id
        )
        return self.mqtt_abstraction.clear_active_exercise_set(session_id)
