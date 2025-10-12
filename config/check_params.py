#!/usr/bin/env python3
"""Check Pixhawk TELEM 2 configuration parameters"""

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

def check_params(connection_string):
    """Check TELEM 2 related parameters"""

    print(f"Connecting to Pixhawk via {connection_string}...")
    mav = mavutil.mavlink_connection(connection_string)

    # Wait for heartbeat
    print("Waiting for heartbeat...")
    mav.wait_heartbeat()
    print(f"Heartbeat received (system {mav.target_system} component {mav.target_component})")

    # Parameters to check
    params_to_check = [
        'MAV_0_CONFIG',
        'MAV_1_CONFIG',
        'MAV_2_CONFIG',
        'SER_TEL1_BAUD',
        'SER_TEL2_BAUD',
        'MAV_0_MODE',
        'MAV_1_MODE',
        'MAV_1_RATE',
    ]

    print("\n" + "=" * 60)
    print("Current Parameters:")
    print("=" * 60)

    for param_name in params_to_check:
        # Request parameter
        mav.mav.param_request_read_send(
            mav.target_system,
            mav.target_component,
            param_name.encode('utf-8'),
            -1
        )

        # Wait for parameter value
        start_time = time.time()
        while time.time() - start_time < 2:
            msg = mav.recv_match(type='PARAM_VALUE', blocking=True, timeout=1)
            if msg:
                # Handle both bytes and str for param_id
                param_id = msg.param_id
                if isinstance(param_id, bytes):
                    param_id = param_id.decode('utf-8').strip('\x00')
                else:
                    param_id = param_id.strip('\x00')

                if param_id == param_name:
                    print(f"{param_name:20} = {msg.param_value}")
                    break
        else:
            print(f"{param_name:20} = (not found)")

    print("\n" + "=" * 60)
    print("Expected values for TELEM 2:")
    print("=" * 60)
    print("MAV_1_CONFIG         = 102 (TELEM 2)")
    print("SER_TEL2_BAUD        = 921600")
    print("MAV_1_MODE           = 0 (Normal) or 2 (Onboard)")
    print("MAV_1_RATE           = 0 (auto) or higher")

    mav.close()

if __name__ == "__main__":
    # Use USB connection (ttyACM0)
    connection = "/dev/ttyACM0,57600"

    if len(sys.argv) > 1:
        connection = sys.argv[1]

    print("=" * 60)
    print("Pixhawk Parameter Check Tool")
    print("=" * 60)
    print(f"Connection: {connection}")
    print()

    try:
        check_params(connection)
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        sys.exit(1)
