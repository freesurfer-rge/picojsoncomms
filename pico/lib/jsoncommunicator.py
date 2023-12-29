import binascii
import json

import machine

import aio_queue

class JSONCommunicator:
    def __init__(self):
        self._incoming = aio_queue.Queue()
        # Get the board's id as a string
        self._id = binascii.hexlify(machine.unique_id()).decode()

    def send(self, obj):
        message = dict(id=self._id, type="user", payload=obj)
        print(json.dumps(message))