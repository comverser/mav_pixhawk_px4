"""MAVLink connection utilities"""
from pymavlink import mavutil
from pymavlink.mavutil import mavlink_connection
from src.mavlink.config import get_connection_address, convert_address_format


def connect(address: str = None) -> mavlink_connection:
    """
    Create MAVLink connection and wait for heartbeat.

    Args:
        address: Connection address. If None, uses DRONE_ADDRESS environment variable.

    Returns:
        mavlink_connection: Connected MAVLink instance.

    Raises:
        ValueError: If address is not provided and DRONE_ADDRESS is not set.
    """
    if address is None:
        address = get_connection_address()

    # Convert MAVSDK format to pymavlink format
    connection_address = convert_address_format(address)

    print(f"Connecting to {connection_address}...")

    # Create MAVLink connection
    mav = mavutil.mavlink_connection(connection_address)

    # Wait for heartbeat
    print("Waiting for heartbeat...")
    mav.wait_heartbeat()
    print(f"Heartbeat from system {mav.target_system}, component {mav.target_component}")

    return mav
