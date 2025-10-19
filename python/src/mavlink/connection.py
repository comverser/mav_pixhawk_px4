"""MAVLink connection utilities"""
from pymavlink import mavutil
from pymavlink.mavutil import mavlink_connection
import os


def get_connection_address() -> str:
    """Get connection address from environment variable."""
    address = os.getenv("DRONE_ADDRESS")
    if not address:
        raise ValueError("DRONE_ADDRESS environment variable not set")
    return address


def convert_mavsdk_to_pymavlink_address(address: str) -> str:
    """
    Convert MAVSDK address format to pymavlink format.

    MAVSDK uses :// separator while pymavlink uses : separator for network connections.
    For serial connections, pymavlink doesn't use a prefix and uses comma for baud rate.

    Examples:
        udpin://0.0.0.0:14540 -> udpin:0.0.0.0:14540
        udpout://0.0.0.0:14540 -> udpout:0.0.0.0:14540
        serial:///dev/ttyACM0:57600 -> /dev/ttyACM0,57600
        serial:/dev/ttyACM0:57600 -> /dev/ttyACM0,57600
    """
    # Handle serial connections: remove serial: prefix and convert last : to ,
    if address.startswith("serial:"):
        # Remove serial:// or serial: prefix
        device_str = address.replace("serial://", "").replace("serial:", "")
        # Replace last colon with comma for baud rate
        if ":" in device_str:
            parts = device_str.rsplit(":", 1)
            return f"{parts[0]},{parts[1]}"
        return device_str

    # Handle network connections: replace :// with :
    return address.replace("://", ":", 1)


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

    connection_address = convert_mavsdk_to_pymavlink_address(address)
    print(f"Connecting to {connection_address}...")

    mav = mavutil.mavlink_connection(connection_address)
    print("Waiting for heartbeat...")
    mav.wait_heartbeat()
    print(f"Heartbeat from system {mav.target_system}, component {mav.target_component}")

    return mav
