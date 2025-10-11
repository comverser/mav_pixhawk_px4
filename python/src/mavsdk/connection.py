"""MAVSDK connection utilities"""
from mavsdk import System
from src.config import get_connection_address


async def connect(address: str = None) -> System:
    """
    Connect to drone via MAVSDK and wait for connection.

    Args:
        address: Connection address. If None, uses DRONE_ADDRESS environment variable.

    Returns:
        System: Connected MAVSDK System instance.

    Raises:
        ValueError: If address is not provided and DRONE_ADDRESS is not set.
    """
    if address is None:
        address = get_connection_address()

    drone = System()
    await drone.connect(system_address=address)

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
