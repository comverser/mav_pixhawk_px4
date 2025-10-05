"""Flight operations"""
import asyncio
from mavsdk import System
from src.core.connection import connect, wait_for_gps


async def takeoff() -> None:
    """Takeoff, hover, and land."""
    d = await connect()
    await wait_for_gps(d)
    print("-- Arming")
    await d.action.arm()
    print("-- Taking off")
    await d.action.takeoff()
    await asyncio.sleep(10)
    print("-- Landing")
    await d.action.land()
