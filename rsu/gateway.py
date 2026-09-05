import json
import os
from collections import deque


class RSUGateway:
    def __init__(self, max_queue_size=1000):
        self.buffer = deque(maxlen=max_queue_size)

    def enqueue(self, packet):
        self.buffer.append(packet)

    def flush(self):
        batch = list(self.buffer)
        self.buffer.clear()
        return batch

    def status(self):
        return {"queue_size": len(self.buffer), "mode": "online" if os.getenv("APP_ENV", "development") == "development" else "offline"}
