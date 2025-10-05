"""Drone connection utilities"""
import os
import sys
from mavsdk import System

DRONE_ADDRESS = os.getenv("DRONE_ADDRESS")


async def connect(address: str = None) -> System:
    """Connect to drone and wait for connection."""
    connection_address = address or DRONE_ADDRESS
    if not connection_address:
        print("Error: DRONE_ADDRESS environment variable not set")
        sys.exit(1)

    drone = System()
    await drone.connect(system_address=connection_address)

    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("Drone connected!")
            break
    return drone


async def wait_for_gps(drone: System) -> None:
    """Wait for GPS lock."""
    print("Waiting for GPS...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            print("GPS OK")
            break
