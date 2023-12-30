import asyncio

import machine

from jsoncommunicator import JSONCommunicator


class BoardBlink:
    def __init__(self, blink_secs: float = 2.0):
        self._half_cycle_secs = blink_secs / 2
        self._board_led = machine.Pin("LED", machine.Pin.OUT)
        self._task = asyncio.create_task(self._blink_runner())

    @property
    def blink_secs(self) -> float:
        return 2 * self._half_cycle_secs

    @blink_secs.setter
    def blink_secs(self, value: float):
        self._half_cycle_secs = value / 2

    async def _blink_runner(self):
        while True:
            self._board_led.toggle()
            await asyncio.sleep(self._half_cycle_secs)


async def main():
    board_blinker = BoardBlink(0.5)

    # This will wait until a message like
    # { "type":"sys", "payload":{ "kind":"SYN" } }
    # is received. The reply will be like:
    # {"sender_id": "e6614103e76c282e", "type": "sys", "payload": {"kind": "ACK"}}
    json_comms = await JSONCommunicator.create()

    board_blinker.blink_secs = 1

    while True:
        nxt_request = await json_comms.get()
        if "a" not in nxt_request or "b" not in nxt_request:
            json_comms.send_log(dict(level="error", message="Keys a and b not present"))
            continue
        c = nxt_request["a"] * nxt_request["b"]
        nxt_request["c"] = c
        json_comms.send(nxt_request)


asyncio.run(main())
