"""Parameter dump utility for Pixhawk"""
from pymavlink import mavutil
import time
import sys
import math


def dump_all_params(port: str = "/dev/ttyACM0", baud: int = 57600, filter_prefix: str = None) -> None:
    """
    Dump all parameters from Pixhawk.

    Args:
        port: Serial port
        baud: Baud rate
        filter_prefix: Optional prefix to filter parameters (e.g., "MAV_", "SERIAL")
    """
    print(f"Connecting to {port} at {baud} baud...")

    try:
        mav = mavutil.mavlink_connection(f"{port},{baud}")
        print("Waiting for heartbeat...")
        mav.wait_heartbeat(timeout=10)
        print(f"Connected to system {mav.target_system}\n")

        # Request all parameters
        print("Requesting all parameters...")
        mav.mav.param_request_list_send(
            mav.target_system,
            mav.target_component
        )

        params = {}
        start_time = time.time()
        timeout = 30  # 30 seconds to receive all parameters

        print("Receiving parameters...\n")

        while time.time() - start_time < timeout:
            msg = mav.recv_match(type='PARAM_VALUE', blocking=True, timeout=1)
            if msg:
                param_id = msg.param_id.strip()
                param_value = msg.param_value
                params[param_id] = param_value

                # Show progress
                if len(params) % 50 == 0:
                    print(f"  Received {len(params)} parameters...")

        print(f"\nReceived {len(params)} total parameters\n")

        # Filter if requested
        if filter_prefix:
            filtered = {k: v for k, v in params.items() if k.startswith(filter_prefix)}
            print(f"Filtered to {len(filtered)} parameters starting with '{filter_prefix}':\n")
            display_params = filtered
        else:
            display_params = params

        # Display parameters
        print("=" * 70)
        for param_id in sorted(display_params.keys()):
            value = display_params[param_id]

            # Try to format nicely
            if isinstance(value, float):
                if math.isnan(value):
                    print(f"{param_id:30s} = NaN")
                elif math.isinf(value):
                    print(f"{param_id:30s} = {'Inf' if value > 0 else '-Inf'}")
                elif value == int(value):
                    print(f"{param_id:30s} = {int(value)}")
                else:
                    print(f"{param_id:30s} = {value:.6f}")
            else:
                print(f"{param_id:30s} = {value}")
        print("=" * 70)

        # Look for TELEM2 related parameters
        print("\nSearching for TELEM2-related parameters...")
        telem_params = {}

        # PX4 patterns
        for key in ['MAV_0_', 'MAV_1_', 'MAV_2_', 'SER_TEL2_']:
            matches = {k: v for k, v in params.items() if k.startswith(key)}
            telem_params.update(matches)

        # ArduPilot patterns
        for key in ['SERIAL1_', 'SERIAL2_', 'SERIAL3_']:
            matches = {k: v for k, v in params.items() if k.startswith(key)}
            telem_params.update(matches)

        if telem_params:
            print(f"\nFound {len(telem_params)} TELEM-related parameters:")
            print("=" * 70)
            for param_id in sorted(telem_params.keys()):
                value = telem_params[param_id]
                if isinstance(value, float):
                    if math.isnan(value):
                        print(f"{param_id:30s} = NaN")
                    elif math.isinf(value):
                        print(f"{param_id:30s} = {'Inf' if value > 0 else '-Inf'}")
                    elif value == int(value):
                        print(f"{param_id:30s} = {int(value)}")
                    else:
                        print(f"{param_id:30s} = {value:.6f}")
                else:
                    print(f"{param_id:30s} = {value}")
            print("=" * 70)
        else:
            print("  No obvious TELEM parameters found")
            print("  Try running with --all to see all parameters")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Dump Pixhawk parameters")
    parser.add_argument('--port', default='/dev/ttyACM0', help='Serial port')
    parser.add_argument('--baud', type=int, default=57600, help='Baud rate')
    parser.add_argument('--filter', help='Filter parameters by prefix (e.g., MAV_, SERIAL)')
    parser.add_argument('--all', action='store_true', help='Show all parameters')

    args = parser.parse_args()

    dump_all_params(args.port, args.baud, args.filter if not args.all else None)
