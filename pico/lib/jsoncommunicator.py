import asyncio
import binascii
import json
import select
import sys

import machine

import aio_queue

class JSONCommunicator:
    def __init__(self):
        self._incoming = aio_queue.Queue()
        self._ready = asyncio.Event()
        self._poll_sleep_secs = 0.01
        # Get the board's id as a string
        self._id = binascii.hexlify(machine.unique_id()).decode()

        self._listen_task = asyncio.create_task(self._listener())

    @property
    def poll_sleep_secs(self):
        return self._poll_sleep_secs
    
    @poll_sleep_secs.setter
    def poll_sleep_secs(self, value):
        self._poll_sleep_secs = value

    async def send(self, obj):
        await self._ready.wait()
        message = dict(sender_id=self._id, type="user", payload=obj)
        print(json.dumps(message))

    def send_log(self, obj):
        message = dict(sender_id=self._id, type="log", payload=obj)
        print(json.dumps(message))


    async def _listener(self):
        poller = select.poll()
        poller.register(sys.stdin, select.POLLIN)

        while True:
            result = poller.poll(0)
            if len(result) > 0:
                poll_tuple = result[0]
                if poll_tuple[1] != select.POLLIN:
                    self.send_log(dict(level="error", message=f"Unexpected poll_tuple[1]: {poll_tuple[1]}"))
                else:
                    json_line = poll_tuple[0].readline()
                    try:
                        recv_obj = json.loads(json_line)
                        await self._handle_received(recv_obj)
                    except Exception as e:
                        self.send_log(dict(level="error", message=f"Failed to decode: {json_line}"))
            await asyncio.sleep(self.poll_sleep_secs)

    async def _handle_received(self, recv_obj):
        # On startup, the 'SYN' message won't know the target_id
        if "target_id" in recv_obj:
            if recv_obj["target_id"] != self._id:
                self.send_log(dict(level="error", message=f"Missent object: {json.dumps(recv_obj)}"))
                return
            
        if "type" not in recv_obj or "payload" not in recv_obj:
            self.send_log(dict(level="error", message=f"Missing type or payload in object: {json.dumps(recv_obj)}"))
            return
        
        if recv_obj["type"] == "user":
            await self._incoming.put(recv_obj["payload"])
        elif recv_obj["type"] == "sys":
            await self._handle_sys(recv_obj["payload"])
        else:
            self.send_log(dict(level="error", message=f"Unrecognised message type: {recv_obj}"))

    async def _handle_sys(self, sys_payload):
        if "kind" not in sys_payload:
            self.send_log(dict(level="error", message=f"Missing kind on sys_payload: {json.dumps(sys_payload)}"))
            return
        
        response = None
        send_ready = False
        if sys_payload["kind"] == "SYN":
            response = dict(kind="ACK")
            send_ready = True
        else:
            self.send_log(dict(level="error", message=f"Unknown kind on sys_payload: {json.dumps(sys_payload)}"))
            return
        
        message = dict(sender_id=self._id, type="sys", payload=response)
        print(json.dumps(message))
        if send_ready:
            self._ready.set()
            