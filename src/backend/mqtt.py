import json
import os
import uuid
from datetime import datetime, timezone
from socket import socket
import paho.mqtt.client as mqtt
from paho.mqtt.packettypes import PacketTypes
from paho.mqtt.properties import Properties
import structlog

# Configure logging
logger = structlog.getLogger(__name__)


class EMGMQTTClient:
    def __init__(self, broker_host, broker_port, message_handler, username=None, password=None,
                 topic_pattern="emg/+/data", transport="websockets", client_id=f"emg-client-{uuid.uuid4()}"):
        """
        Initialize the MQTT client for EMG data.

        Args:
            broker_host: MQTT broker hostname or IP
            broker_port: MQTT broker port
            message_handler: Callback function or object method to handle MQTT messages
            username: MQTT broker username (optional)
            password: MQTT broker password (optional)
            topic_pattern: Topic pattern to subscribe to (default: "emg/+/data")
                           The '+' is a wildcard for any single topic level
                           The '#' is a wildcard for multiple topic levels
            transport: Transport protocol ("websockets" or "tcp")
        """
        # Create client using MQTT v5 protocol and specified transport
        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id,
            transport=transport
        )

        # Set up callbacks
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

        # Set credentials if provided. Not needed for local broker setup
        if username and password:
            self.client.username_pw_set(username, password)

        self.broker_host = broker_host
        self.broker_port = broker_port
        self.transport = transport
        self.message_handler = message_handler
        self.topic_pattern = topic_pattern

    def connect(self):
        """Connect to the MQTT broker and start the loop."""
        try:
            # Ensure port is an integer
            port = int(self.broker_port) if not isinstance(self.broker_port, int) else self.broker_port
            logger.info(f"Attempting to connect to MQTT broker at {self.broker_host}:{port}")

            # Handle WebSocket URL with path (ws://host:port/path)
            if self.transport == "websockets" and self.broker_host.startswith(('ws://', 'wss://')):
                # Parse the WebSocket URL to extract components
                url_parts = self.broker_host.split('://', 1)

                # Handle path component if present
                remaining = url_parts[1]
                if '/' in remaining:
                    host_port, path = remaining.split('/', 1)
                    path = '/' + path
                else:
                    host_port = remaining
                    path = ''

                # Handle port in URL if present
                if ':' in host_port:
                    host, url_port = host_port.split(':', 1)
                    # If port is in URL, use it instead of the separate port parameter
                    try:
                        port = int(url_port)
                    except ValueError:
                        logger.warning(f"Invalid port in URL: {url_port}, using provided port: {port}")
                else:
                    host = host_port

                logger.info(f"Parsed WebSocket URL: host={host}, port={port}, path={path}")

                # Set WebSocket path if present
                if path:
                    self.client.ws_set_options(path=path)

                # Use the extracted host, not the full URL
                broker_address = host
            else:
                # Regular TCP connection or simple hostname
                broker_address = self.broker_host

            # Connect to the broker
            self.client.connect(broker_address, port, 60)
            self.client.loop_start()
            logger.info(f"Successfully connected to MQTT broker at {broker_address}:{port}")
        except socket.gaierror as e:
            # Handle DNS resolution errors specifically
            logger.error(f"Unable to resolve hostname '{self.broker_host}'. Error: {e}")
            logger.info("Check that the broker address is correct and network connectivity is available.")
            raise
        except ConnectionRefusedError as e:
            # Handle connection refused errors
            logger.error(f"Connection refused to {self.broker_host}:{port}. Error: {e}")
            logger.info("Check that the broker is running and the port is correct.")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            raise

    def on_connect(self, client, userdata, flags, rc, properties=None):
        """Callback when connected to the MQTT broker (API v2 signature)."""
        if rc == 0:
            logger.info("Successfully connected to MQTT broker")
            # Subscribe to EMG data topics using the configured pattern
            client.subscribe(self.topic_pattern)
            logger.info(f"Subscribed to topic: {self.topic_pattern}")
        else:
            logger.error(f"Connection to MQTT broker failed with code {rc}")

    def on_message(self, client, userdata, msg):
        """Callback when a message is received from the broker (API v2 signature).

        Args:
            client: The client instance for this callback
            userdata: The private user data as set in Client() or userdata_set()
            msg: An instance of MQTTMessage with topic and payload
        """
        try:
            logger.debug(f"Received message on topic {msg.topic}")

            # Parse the payload
            try:
                # Try to decode JSON payload
                try:
                    payload = json.loads(msg.payload.decode())
                except json.JSONDecodeError:
                    # If not valid JSON, use raw payload
                    payload = msg.payload.decode()

                # Create message data with topic and payload
                message_data = {
                    "topic": msg.topic,
                    "payload": payload,
                    "qos": msg.qos,
                    "retain": msg.retain,
                    "timestamp": datetime.now(timezone.utc)
                }

                # Pass the raw message to the handler
                # The handler could be either a function or an object with methods
                # Try to handle it in a generic way
                if hasattr(self.message_handler, 'add_emg_data'):
                    # Object with add_emg_data method (abstraction layer)
                    self.message_handler.add_emg_data(message_data["payload"])
                elif callable(self.message_handler):
                    # Function handler
                    self.message_handler(message_data)
                else:
                    logger.warning(f"Unknown message handler type: {type(self.message_handler)}")

                logger.debug(f"Processed message from topic: {msg.topic}")

            except Exception as e:
                logger.error(f"Error processing payload: {e}", exc_info=True)

        except Exception as e:
            logger.error(f"Error in message callback: {e}", exc_info=True)

    def on_disconnect(self, client, userdata, rc, properties=None):
        """Callback when disconnected from the broker (API v2 signature)."""
        if rc != 0:
            logger.warning(f"Unexpected disconnection from MQTT broker with code {rc}")
        else:
            logger.info("Disconnected from MQTT broker")

    def publish(self, topic, payload, qos=0, retain=False, properties=None):
        """
        Publish a message to the MQTT broker.

        Args:
            topic: The topic to publish to
            payload: The message payload (can be a dict, will be converted to JSON)
            qos: Quality of Service (0, 1, or 2)
            retain: Whether to retain the message on the broker
            properties: MQTT v5 properties (optional)

        Returns:
            The message info (MQTTMessageInfo) for tracking delivery
        """
        try:
            # Convert dict payload to JSON string
            if isinstance(payload, dict):
                payload = json.dumps(payload)

            # Create properties object if using MQTT v5
            mqtt_properties = Properties(PacketTypes.PUBLISH) if properties is None else properties

            # Publish the message
            result = self.client.publish(topic, payload, qos=qos, retain=retain, properties=mqtt_properties)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Published message to {topic}: {payload}")
            else:
                logger.error(f"Failed to publish message to {topic}, error code: {result.rc}")

            return result
        except Exception as e:
            logger.error(f"Error publishing message: {e}")
            raise

    def disconnect(self):
        """Disconnect from the MQTT broker."""
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("Disconnected from MQTT broker")
