#!/usr/bin/env python3
"""Configure PX4 TELEM 2 for MAVLink at 921600 baud"""

import sys
import os

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

import time
from pymavlink import mavutil

def configure_telem2(connection_string):
    """Configure TELEM 2 port on Pixhawk"""

    print(f"Connecting to Pixhawk via {connection_string}...")
    mav = mavutil.mavlink_connection(connection_string)

    # Wait for heartbeat
    print("Waiting for heartbeat...")
    mav.wait_heartbeat()
    print(f"Heartbeat received (system {mav.target_system} component {mav.target_component})")

    # Set MAV_1_CONFIG to TELEM 2 (102)
    print("\nSetting MAV_1_CONFIG to TELEM 2 (102)...")
    mav.mav.param_set_send(
        mav.target_system,
        mav.target_component,
        b'MAV_1_CONFIG',
        102,
        mavutil.mavlink.MAV_PARAM_TYPE_INT32
    )
    time.sleep(0.5)

    # Set SER_TEL2_BAUD to 921600
    print("Setting SER_TEL2_BAUD to 921600...")
    mav.mav.param_set_send(
        mav.target_system,
        mav.target_component,
        b'SER_TEL2_BAUD',
        921600,
        mavutil.mavlink.MAV_PARAM_TYPE_INT32
    )
    time.sleep(0.5)

    print("\nConfiguration sent. Please reboot Pixhawk for changes to take effect.")
    print("You can reboot via: reboot command or power cycle")

    mav.close()

if __name__ == "__main__":
    # Use USB connection (ttyACM0)
    connection = "/dev/ttyACM0,57600"

    if len(sys.argv) > 1:
        connection = sys.argv[1]

    print("=" * 60)
    print("PX4 TELEM 2 Configuration Tool")
    print("=" * 60)
    print(f"Connection: {connection}")
    print()

    try:
        configure_telem2(connection)
        print("\n✓ Configuration complete!")
        print("\nNext steps:")
        print("  1. Reboot Pixhawk (power cycle or reboot command)")
        print("  2. Run: just cpp-run")
        print("  3. Select option 2 for TELEM 2")
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        sys.exit(1)
