"""Environment variable utilities"""
import os


def get_connection_address() -> str:
    """Get connection address from DRONE_ADDRESS environment variable.

    Returns:
        str: Connection address string

    Raises:
        ValueError: If DRONE_ADDRESS environment variable is not set
    """
    address = os.getenv("DRONE_ADDRESS")
    if not address:
        raise ValueError("DRONE_ADDRESS environment variable not set")
    return address
