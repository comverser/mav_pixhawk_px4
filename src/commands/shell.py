"""PX4 shell command utilities"""
import asyncio
from mavsdk import System
from src.core.connection import connect


async def execute(command: str) -> None:
    """Send shell command to PX4."""
    d = await connect()
    print(f"Command: {command}")
    receive_task = asyncio.create_task(_receive_output(d))
    await asyncio.sleep(0.5)
    await d.shell.send(command)
    try:
        await asyncio.wait_for(receive_task, timeout=5)
    except asyncio.TimeoutError:
        pass


async def _receive_output(drone: System) -> None:
    """Receive shell output."""
    start = asyncio.get_event_loop().time()
    async for output in drone.shell.receive():
        if output:
            print(f"Shell: {output}", end='')
        if asyncio.get_event_loop().time() - start > 3:
            break
