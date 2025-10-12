#!/usr/bin/env python3
"""Reboot Pixhawk via MAVLink command"""

import sys
import os
import time

# Add python venv to path
script_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(script_dir)
venv_path = os.path.join(parent_dir, 'python', 'venv', 'lib', 'python3.11', 'site-packages')
if os.path.exists(venv_path):
    sys.path.insert(0, venv_path)
else:
    # Try python3.12
    venv_path = os.path.join(parent_dir, 'python', 'venv', 'lib', 'python3.12', 'site-packages')
    if os.path.exists(venv_path):
        sys.path.insert(0, venv_path)

from pymavlink import mavutil

def reboot_pixhawk(connection_string):
    """Send reboot command to Pixhawk"""

    print(f"Connecting to Pixhawk via {connection_string}...")
    mav = mavutil.mavlink_connection(connection_string)

    # Wait for heartbeat
    print("Waiting for heartbeat...")
    mav.wait_heartbeat()
    print(f"Heartbeat received (system {mav.target_system} component {mav.target_component})")

    # Send reboot command
    print("\nSending reboot command...")
    mav.mav.command_long_send(
        mav.target_system,
        mav.target_component,
        mavutil.mavlink.MAV_CMD_PREFLIGHT_REBOOT_SHUTDOWN,
        0,  # confirmation
        1,  # param1: 1 = reboot autopilot
        0, 0, 0, 0, 0, 0  # param2-7: unused
    )

    print("Reboot command sent. Pixhawk will reboot now.")
    time.sleep(1)

    mav.close()

if __name__ == "__main__":
    # Use USB connection (ttyACM0)
    connection = "/dev/ttyACM0,57600"

    if len(sys.argv) > 1:
        connection = sys.argv[1]

    print("=" * 60)
    print("Pixhawk Reboot Tool")
    print("=" * 60)
    print(f"Connection: {connection}")
    print()

    try:
        reboot_pixhawk(connection)
        print("\n✓ Reboot command sent successfully!")
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        sys.exit(1)
