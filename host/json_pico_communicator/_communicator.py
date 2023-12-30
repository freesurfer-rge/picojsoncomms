import asyncio
import io
import json
import logging
import os
import pathlib
import queue
import threading
import time

_logger = logging.getLogger("JSONCommunicator")


class JSONCommunicator:
    def __init__(self, pico_path: pathlib.Path):
        self._tty = io.TextIOWrapper(
            io.FileIO(os.open(pico_path, os.O_NOCTTY | os.O_RDWR), "r+"),
            line_buffering=True,
        )
        self._loop = asyncio.get_running_loop()
        self._incoming = asyncio.Queue()
        self._pico_id = None
        self._thread = None

    @property
    def pico_id(self)-> str:
        return self._pico_id


    def _tty_reader(self):
        for line in iter(self._tty.readline, None):
            actual = line.strip()
            if actual:
                try:
                    actual_obj = json.loads(actual)
                    self._handle_incoming(actual_obj)
                except Exception as e:
                    _logger.error(f"Caught exception {e} for {actual}")
            else:
                time.sleep(0.01)

    def _handle_incoming(self, incoming_obj: dict[str,any]):
        if "sender_id" not in incoming_obj:
            _logger.error(f"sender_id missing: {incoming_obj}")
            return
        
        if incoming_obj["sender_id"] != self.pico_id:
            _logger.error(f"Bad sender_id: {incoming_obj}")
            return
        
        if "type" not in incoming_obj or "payload" not in incoming_obj:
            _logger.error(f"Missing type or payload: {incoming_obj}")
            return
        
        if incoming_obj["type"] == "user":
            asyncio.run_coroutine_threadsafe(self._incoming.put(incoming_obj["payload"]), self._loop)
        elif incoming_obj["type"] == "log":
            _logger.info(f"Received from Pico: {incoming_obj}")
        else:
            _logger.error(f"Unsupported message type: {incoming_obj}")

    @classmethod
    async def create(cls, pico_path: pathlib.Path) -> 'JSONCommunicator':
        comm = JSONCommunicator(pico_path)
        syn_msg = dict(type="sys", payload=dict(kind="SYN"))
        comm._tty.write(json.dumps(syn_msg) + "\n")
        response = comm._tty.readline()
        _logger.info(f"Response: {response}")
        resp_obj = json.loads(response)
        comm._pico_id = resp_obj["sender_id"]
        assert resp_obj["type"]=="sys"
        assert resp_obj["payload"]["kind"] =="ACK"
        _logger.info(f"Established communcation with {comm.pico_id}")

        comm._thread = threading.Thread(target=comm._tty_reader)
        comm._thread.start()

        return comm