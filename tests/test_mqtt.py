from backend.mqtt.consumer import IoTMQTTConsumer


def test_mqtt_consumer_initializes():
    consumer = IoTMQTTConsumer()
    assert consumer is not None
    assert hasattr(consumer, 'client')
