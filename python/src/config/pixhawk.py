"""Pixhawk configuration and diagnostics utilities"""
from pymavlink import mavutil


def test_connection(port: str, baud: int = 57600, timeout: int = 10) -> bool:
    """
    Test if Pixhawk is connected on given serial port.

    Args:
        port: Serial port path (e.g., /dev/ttyAMA0)
        baud: Baud rate (default: 57600 for TELEM2)
        timeout: Heartbeat timeout in seconds

    Returns:
        bool: True if connection successful, False otherwise
    """
    print(f"\nTesting {port} at {baud} baud...")

    try:
        mav = mavutil.mavlink_connection(f"{port},{baud}")
        print(f"Waiting for heartbeat (timeout: {timeout}s)...")

        msg = mav.wait_heartbeat(timeout=timeout)

        if msg:
            print(f"Connection successful!")
            print(f"  System ID: {mav.target_system}")
            print(f"  Component ID: {mav.target_component}")
            print(f"  MAVLink version: {msg.mavlink_version}")
            print(f"  Autopilot: {msg.autopilot}")
            print(f"  Vehicle type: {msg.type}")
            return True
        else:
            print(f"No heartbeat received")
            return False

    except Exception as e:
        print(f"Error: {e}")
        return False


def scan_ports() -> None:
    """Scan common serial ports for Pixhawk connection."""
    ports_to_test = ["/dev/ttyAMA0", "/dev/ttyAMA10", "/dev/ttyACM0", "/dev/ttyUSB0"]

    print("Scanning for Pixhawk on serial ports...")
    print("=" * 50)

    for port in ports_to_test:
        if test_connection(port):
            print(f"\nPixhawk found on {port}")
            return

    print("\nNo Pixhawk found on any port")
    print("\nTroubleshooting:")
    print("1. Check physical connection to TELEM2")
    print("2. Verify TELEM2 is enabled in Pixhawk parameters (MAV_1_CONFIG)")
    print("3. Check baud rate matches (default: 57600)")
