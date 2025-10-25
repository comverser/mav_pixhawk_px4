"""Heartbeat monitoring for MAVLink"""
from pymavlink import mavutil
import time


def monitor_heartbeat(connection_string: str, duration: float = 10.0) -> None:
    """
    Monitor heartbeat messages continuously.

    Args:
        connection_string: MAVLink connection string (e.g., "/dev/ttyACM0,57600")
        duration: Duration to monitor in seconds
    """
    print(f"Connecting to {connection_string}...")
    print("Waiting for heartbeat...")

    mav = None
    msg = None

    try:
        # Retry connection a few times with delays
        for attempt in range(3):
            try:
                mav = mavutil.mavlink_connection(connection_string)
                msg = mav.wait_heartbeat(timeout=10)
                if msg:
                    break
                if attempt < 2:
                    print("No heartbeat, retrying...")
                    time.sleep(2)
            except Exception as e:
                if attempt < 2:
                    print(f"Connection error, retrying... ({e})")
                    time.sleep(2)
                else:
                    raise

        if not msg or not mav:
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
