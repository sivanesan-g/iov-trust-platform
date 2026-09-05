import json
import logging
import os
import threading
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

from backend.config import MQTT_CANONICAL_TOPIC, MQTT_HOST, MQTT_PORT, MQTT_TOPIC
from backend.security.validation import validate_telemetry
from backend.trust_service import TrustService, analyze_vehicle_status

logger = logging.getLogger(__name__)


class IoTMQTTConsumer:
    def __init__(self, app=None, service=None):
        self.app = app
        self.service = service or TrustService()
        self.client = mqtt.Client(client_id="iov-consumer")
        self.connected = False
        self._lock = threading.Lock()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            logger.info("MQTT connected")
            topic = MQTT_TOPIC.replace("+", "#") if "+" in MQTT_TOPIC else MQTT_TOPIC
            client.subscribe(topic, qos=1)
        else:
            self.connected = False
            logger.warning("MQTT connection failed rc=%s", rc)

    def _on_disconnect(self, client, userdata, rc):
        self.connected = False
        logger.warning("MQTT disconnected rc=%s", rc)

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            ok, details = validate_telemetry(payload)
            if not ok:
                logger.warning("Rejected telemetry: %s", details)
                return
            vehicle_id = payload["vehicle_id"]
            result = self.service.process_telemetry(payload)
            logger.info("Processed telemetry for %s -> %s", vehicle_id, result.get("status"))
        except Exception as exc:
            logger.exception("MQTT processing error: %s", exc)

    def start(self):
        self.client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
        self.client.loop_start()
        while not self.connected:
            time.sleep(0.2)

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()
