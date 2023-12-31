import argparse
import asyncio
import logging
import pathlib

from json_pico_communicator import JSONCommunicator

_logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--pico_device",
        type=pathlib.Path,
        help="Path (in /dev/) to the Pico",
        required=True,
    )

    args = parser.parse_args()
    return args


async def main():
    args = parse_args()
    _logger.info(f"pico_device: {args.pico_device}")

    comm = await JSONCommunicator.create(args.pico_device)
    _logger.info("Comms established")

    done = False
    while not done:
        a = int(input("Enter a: "))
        b = int(input("Enter b: "))
        send = dict(a=a, b=b)
        comm.send(send)
        resp = await comm.get()
        print(f"Result: {resp['c']}")


if __name__ == "__main__":
    asyncio.run(main())
