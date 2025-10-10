"""MAVSDK configuration"""
import os


def get_connection_address() -> str:
    """Get MAVSDK connection address from environment variable."""
    address = os.getenv("DRONE_ADDRESS")
    if not address:
        raise ValueError("DRONE_ADDRESS environment variable not set")
    return address
