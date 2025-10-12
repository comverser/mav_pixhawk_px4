#!/usr/bin/env python3
"""List all Pixhawk parameters (useful for finding correct parameter names)"""

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

def list_params(connection_string, filter_text=None):
    """List all parameters or filtered parameters"""

    print(f"Connecting to Pixhawk via {connection_string}...")
    mav = mavutil.mavlink_connection(connection_string)

    # Wait for heartbeat
    print("Waiting for heartbeat...")
    mav.wait_heartbeat()
    print(f"Heartbeat received (system {mav.target_system} component {mav.target_component})")

    # Request all parameters
    print("\nRequesting parameter list...")
    mav.mav.param_request_list_send(
        mav.target_system,
        mav.target_component
    )

    # Collect parameters
    params = {}
    print("Receiving parameters...")
    start_time = time.time()

    while time.time() - start_time < 10:  # 10 second timeout
        msg = mav.recv_match(type='PARAM_VALUE', blocking=True, timeout=1)
        if msg:
            # Handle both bytes and str for param_id
            param_id = msg.param_id
            if isinstance(param_id, bytes):
                param_id = param_id.decode('utf-8').strip('\x00')
            else:
                param_id = param_id.strip('\x00')

            params[param_id] = msg.param_value

            # Print progress
            if len(params) % 50 == 0:
                print(f"  Received {len(params)} parameters...")

    print(f"\nTotal parameters received: {len(params)}")

    # Filter and display
    if filter_text:
        print(f"\nParameters matching '{filter_text}':")
        print("=" * 60)
        filtered = {k: v for k, v in sorted(params.items()) if filter_text.upper() in k.upper()}
        for name, value in filtered.items():
            print(f"{name:20} = {value}")
    else:
        print("\nAll parameters:")
        print("=" * 60)
        for name, value in sorted(params.items()):
            print(f"{name:20} = {value}")

    mav.close()

if __name__ == "__main__":
    connection = "/dev/ttyACM0,57600"
    filter_text = None

    if len(sys.argv) > 1:
        filter_text = sys.argv[1]

    print("=" * 60)
    print("Pixhawk Parameter List Tool")
    print("=" * 60)
    print(f"Connection: {connection}")
    if filter_text:
        print(f"Filter: {filter_text}")
    print()

    try:
        list_params(connection, filter_text)
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
