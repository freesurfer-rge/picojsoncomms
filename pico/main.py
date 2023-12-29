import asyncio

import machine


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

    while True:
        await asyncio.sleep(10)
        board_blinker.blink_secs = board_blinker.blink_secs * 0.9


asyncio.run(main())
