"""Configuration module for MAVLink connection and Pixhawk diagnostics"""
from src.config.connection import get_connection_address, convert_mavsdk_to_pymavlink_address
from src.config.pixhawk import test_connection, scan_ports

__all__ = [
    "get_connection_address",
    "convert_mavsdk_to_pymavlink_address",
    "test_connection",
    "scan_ports",
]
