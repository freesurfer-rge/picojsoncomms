import asyncio

import machine

from jsoncommunicator import JSONCommunicator


class BoardBlink:
    def __init__(self):
        self._half_cycle_secs = 1.0
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
    board_blinker = BoardBlink()

    # This will wait until a message like
    # { "type":"sys", "payload":{ "kind":"SYN" } }
    # is received. The reply will be like:
    # {"sender_id": "e6614103e76c282e", "type": "sys", "payload": {"kind": "ACK"}}
    json_comms = await JSONCommunicator.create()

    it_count = 0
    while True:
        await asyncio.sleep(10)
        await json_comms.send(dict(it_count=it_count))
        it_count += 1


asyncio.run(main())
