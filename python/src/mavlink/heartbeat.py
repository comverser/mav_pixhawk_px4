"""Heartbeat monitoring and connection testing for MAVLink"""
from pymavlink import mavutil
from pymavlink.mavutil import mavlink_connection
import time


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
    # (port, baud_rate) tuples
    ports_to_test = [
        ("/dev/ttyACM0", 57600),    # USB connection
        ("/dev/ttyAMA10", 921600),  # GPIO UART (TELEM2)
        ("/dev/ttyAMA0", 57600),    # Alternative UART
        ("/dev/ttyUSB0", 57600),    # USB-to-serial adapter
    ]

    print("Scanning for Pixhawk on serial ports...")
    print("=" * 50)

    for port, baud in ports_to_test:
        if test_connection(port, baud):
            print(f"\nPixhawk found on {port} at {baud} baud")
            return

    print("\nNo Pixhawk found on any port")
    print("\nTroubleshooting:")
    print("1. Check physical connection to TELEM2")
    print("2. Verify TELEM2 is enabled in Pixhawk parameters (MAV_1_CONFIG)")
    print("3. Check baud rate matches (USB: 57600, TELEM2: 921600)")


def monitor_heartbeat(connection_string: str, duration: float = 10.0) -> None:
    """
    Monitor heartbeat messages continuously.

    Args:
        connection_string: MAVLink connection string (e.g., "/dev/ttyACM0,57600")
        duration: Duration to monitor in seconds
    """
    print(f"Connecting to {connection_string}...")
    print("Waiting for heartbeat...")

    try:
        mav = mavutil.mavlink_connection(connection_string)
        msg = mav.wait_heartbeat(timeout=10)

        if not msg:
            print("No heartbeat received")
            return

        print(f"Connected to system {mav.target_system}")
        print(f"  Component ID: {mav.target_component}")
        print(f"  MAVLink version: {msg.mavlink_version}")
        print(f"  Autopilot: {msg.autopilot}")
        print(f"  Vehicle type: {msg.type}")
        print()
        print(f"Monitoring heartbeat for {duration} seconds...")
        print("=" * 70)

    except Exception as e:
        print(f"Error: {e}")
        return

    start_time = time.time()
    last_heartbeat = start_time
    heartbeat_count = 0

    while time.time() - start_time < duration:
        msg = mav.recv_match(type='HEARTBEAT', blocking=True, timeout=2)

        if msg:
            now = time.time()
            interval = now - last_heartbeat
            last_heartbeat = now
            heartbeat_count += 1

            # Decode system status
            status_map = {
                0: "UNINIT",
                1: "BOOT",
                2: "CALIBRATING",
                3: "STANDBY",
                4: "ACTIVE",
                5: "CRITICAL",
                6: "EMERGENCY",
                7: "POWEROFF",
                8: "FLIGHT_TERMINATION"
            }
            status = status_map.get(msg.system_status, f"UNKNOWN({msg.system_status})")

            # Decode base mode (armed/disarmed)
            armed = "ARMED" if msg.base_mode & 0b10000000 else "DISARMED"

            print(f"[{heartbeat_count:3d}] Interval: {interval:.2f}s | "
                  f"Status: {status:20s} | {armed}")
        else:
            print("Heartbeat timeout (2s)")

    print("=" * 70)
    print(f"Received {heartbeat_count} heartbeats in {duration:.1f} seconds")
    if heartbeat_count > 0:
        print(f"Average rate: {heartbeat_count / duration:.2f} Hz")
