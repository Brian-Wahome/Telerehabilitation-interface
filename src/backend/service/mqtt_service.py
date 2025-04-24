import uuid

import structlog
from src.backend.mqtt import EMGMQTTClient
from ..exceptions import MQTTClientNotFound


class MQTTService:
    def __init__(self):
        self.mqtt_clients = {}
        self.logger = structlog.get_logger(__name__)
        self.active_subscriptions = {}

    def setup_mqtt_client(self, broker_host="localhost", broker_port=8083, username=None, password=None,
                          topic_pattern="emg/+/+/data", transport="websockets", client_id="emg-client",
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

    def get_client(self, client_id="default"):
        """Get a specific MQTT client"""
        if client_id not in self.mqtt_clients:
            self.logger.error(
                f"MQTT client with ID '{client_id}' not found",
                mqtt_client_id=client_id,
            )
            raise MQTTClientNotFound(f"MQTT client with ID '{client_id}' not found")
        return self.mqtt_clients[client_id]

    def disconnect_client(self, client_id="emg-client"):
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

    def set_active_exercise_set(self, session_id: str, exercise_set_id: str, client_id="default"):
        """
        Set the active exercise set for a session and start MQTT subscription

        Args:
            session_id: The session ID
            exercise_set_id: The exercise set ID
            client_id: MQTT client ID to use
        """
        self.logger.info(
            "Setting active exercise set and starting MQTT subscription",
            session_id=session_id,
            exercise_set_id=exercise_set_id,
            client_id=client_id
        )

        # Get the MQTT client
        client = self.get_client(client_id)

        # Create topic pattern for this session's sensors
        # This assumes sensors are identifiable by session ID in the topic
        # Adjust the pattern based on your actual topic structure
        topic_pattern = f"emg/{session_id}/+/data"

        # Subscribe to the topic pattern
        client.subscribe(topic_pattern)

        # Store subscription info
        self.active_subscriptions[session_id] = {
            "client_id": client_id,
            "exercise_set_id": exercise_set_id,
            "topic_pattern": topic_pattern
        }

        # Set the active exercise set in the abstraction layer
        return self.mqtt_abstraction.set_active_exercise_set(session_id, exercise_set_id)

    def clear_active_exercise_set(self, session_id: str):
        """
        Clear the active exercise set for a session and stop MQTT subscription

        Args:
            session_id: The session ID
        """
        self.logger.info(
            "Clearing active exercise set and stopping MQTT subscription",
            session_id=session_id
        )

        # Check if there's an active subscription for this session
        if session_id in self.active_subscriptions:
            subscription = self.active_subscriptions[session_id]
            client_id = subscription["client_id"]
            topic_pattern = subscription["topic_pattern"]

            try:
                # Get the client
                client = self.get_client(client_id)

                # Unsubscribe from the topic pattern
                client.unsubscribe(topic_pattern)

                self.logger.info(
                    "Unsubscribed from topic pattern",
                    session_id=session_id,
                    topic_pattern=topic_pattern
                )

                # Remove from active subscriptions
                del self.active_subscriptions[session_id]

            except MQTTClientNotFound:
                self.logger.warning(
                    "Client not found for unsubscription",
                    session_id=session_id,
                    client_id=client_id
                )
            except Exception as e:
                self.logger.error(
                    "Error unsubscribing from topic",
                    session_id=session_id,
                    topic_pattern=topic_pattern,
                    error=str(e)
                )

        # Clear the active exercise set in the abstraction layer
        return self.mqtt_abstraction.clear_active_exercise_set(session_id)
