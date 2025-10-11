"""Shared configuration utilities"""
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

    Examples:
        udpin://0.0.0.0:14540 -> udpin:0.0.0.0:14540
        udpout://0.0.0.0:14540 -> udpout:0.0.0.0:14540
    """
    if address.startswith("udpin://"):
        return address.replace("udpin://", "udpin:")
    elif address.startswith("udpout://"):
        return address.replace("udpout://", "udpout:")
    return address
