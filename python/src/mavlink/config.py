"""Pixhawk configuration utilities"""
from pymavlink import mavutil
import time
import os
import glob

from src.common.constants import (
    HEARTBEAT_TIMEOUT,
    COMMAND_ACK_TIMEOUT,
    PARAMETER_READ_TIMEOUT,
    REBOOT_WAIT_SECONDS,
    DEVICE_POLL_ATTEMPTS,
    RECONNECT_ATTEMPTS,
)
from src.mavlink.parameters import encode_param_value, decode_param_value


def _connect(port: str, baud: int):
    """Connect to Pixhawk and wait for heartbeat."""
    print(f"Connecting to {port} at {baud} baud...")
    mav = mavutil.mavlink_connection(f"{port},{baud}")
    print("Waiting for heartbeat...")
    mav.wait_heartbeat(timeout=HEARTBEAT_TIMEOUT)
    print(f"Connected to system {mav.target_system}\n")
    return mav


def _send_command_long(mav, command: int, params: list[float], success_msg: str, fail_msg: str) -> bool:
    """Send MAVLink command and check ACK."""
    mav.mav.command_long_send(
        mav.target_system,
        mav.target_component,
        command,
        0, *params
    )
    msg = mav.recv_match(type='COMMAND_ACK', blocking=True, timeout=COMMAND_ACK_TIMEOUT)
    if msg and msg.result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
        print(success_msg)
        return True
    else:
        print(fail_msg)
        return False


def reset_params(port: str, baud: int) -> None:
    """Reset all parameters to factory defaults."""
    try:
        mav = _connect(port, baud)

        print("⚠ WARNING: This will reset ALL parameters to factory defaults!")
        confirm = input("Type 'RESET' to confirm: ")
        if confirm != "RESET":
            print("Cancelled.")
            return

        print("\nResetting all parameters to defaults...")
        if not _send_command_long(
            mav,
            mavutil.mavlink.MAV_CMD_PREFLIGHT_STORAGE,
            [2, 0, 0, 0, 0, 0, 0],
            "✓ Parameters reset to defaults",
            "✗ Reset command failed"
        ):
            return

        print("\n✓ All parameters reset. Reboot Pixhawk to apply changes.")

    except Exception as e:
        print(f"Error: {e}")


def reboot(port: str, baud: int) -> None:
    """Reboot Pixhawk and verify it comes back online."""
    try:
        mav = _connect(port, baud)

        print("Sending reboot command...")
        if not _send_command_long(
            mav,
            mavutil.mavlink.MAV_CMD_PREFLIGHT_REBOOT_SHUTDOWN,
            [1, 0, 0, 0, 0, 0, 0],
            "✓ Reboot command accepted",
            "✗ Reboot command failed"
        ):
            return

        print("\nWaiting for connection to drop...", end="", flush=True)
        time.sleep(2)

        try:
            for i in range(10):
                msg = mav.recv_match(type='HEARTBEAT', blocking=False, timeout=0.5)
                if not msg:
                    print(" ✓ Connection dropped")
                    break
                print(".", end="", flush=True)
                time.sleep(0.5)
            else:
                print(" ⚠ Connection still alive")
        except Exception:
            # Serial disconnect during reboot is expected
            print(" ✓ Connection dropped")

        print(f"Waiting for Pixhawk to boot ({REBOOT_WAIT_SECONDS}s)...", end="", flush=True)
        for _ in range(REBOOT_WAIT_SECONDS):
            time.sleep(1)
            print(".", end="", flush=True)
        print()

        print("\nWaiting for device to reappear...", end="", flush=True)
        device_found = False
        new_port = None

        # Check if port is a USB ACM device
        is_usb_acm = port.startswith('/dev/ttyACM')

        for _ in range(DEVICE_POLL_ATTEMPTS):
            if is_usb_acm:
                # For USB devices, check for any /dev/ttyACM* device
                acm_devices = glob.glob('/dev/ttyACM*')
                if acm_devices:
                    new_port = acm_devices[0]
                    print(f" ✓ Device found at {new_port}")
                    device_found = True
                    break
            else:
                # For other devices (like UART), check exact path
                if os.path.exists(port):
                    new_port = port
                    print(" ✓ Device found")
                    device_found = True
                    break
            print(".", end="", flush=True)
            time.sleep(1)

        if not device_found:
            print(f" ✗ Device did not reappear")
            return

        print("Reconnecting...", end="", flush=True)
        for attempt in range(RECONNECT_ATTEMPTS):
            try:
                time.sleep(1)
                mav = mavutil.mavlink_connection(f"{new_port},{baud}")
                msg = mav.wait_heartbeat(timeout=HEARTBEAT_TIMEOUT)
                if msg:
                    print(" ✓")
                    print(f"✓ Pixhawk rebooted successfully!")
                    print(f"  System ID: {mav.target_system}")
                    if new_port != port:
                        print(f"  Device path changed: {port} → {new_port}")
                    return
            except Exception:
                print(".", end="", flush=True)

        print(" ✗")
        print("✗ Failed to reconnect after reboot")

    except Exception as e:
        print(f"Error: {e}")


def read_telem2_params(port: str, baud: int) -> None:
    """Read and display current MAV_1_* parameter values."""
    try:
        mav = _connect(port, baud)

        params = ['MAV_1_CONFIG', 'MAV_1_MODE', 'MAV_1_FLOW_CTRL', 'MAV_1_FORWARD', 'MAV_1_RATE']
        param_values = {}

        print("Reading current MAV_1_* parameters...\n")

        # Allow connection to stabilize
        time.sleep(0.5)

        # Try up to 3 times to get all parameters
        for attempt in range(3):
            # Request any missing parameters
            missing_params = [p for p in params if p not in param_values]
            if not missing_params:
                break

            if attempt > 0:
                print(f"Retry {attempt}: requesting {len(missing_params)} missing parameter(s)...")

            for param_name in missing_params:
                mav.mav.param_request_read_send(
                    mav.target_system,
                    mav.target_component,
                    param_name.encode('utf-8'),
                    -1
                )
                time.sleep(0.15)  # Longer delay to avoid overwhelming

            # Collect responses
            timeout = time.time() + 3
            while time.time() < timeout:
                msg = mav.recv_match(type='PARAM_VALUE', blocking=False, timeout=0.5)
                if msg:
                    param_id = msg.param_id.decode('utf-8') if isinstance(msg.param_id, bytes) else msg.param_id
                    param_id = param_id.rstrip('\x00')
                    if param_id in params and param_id not in param_values:
                        int_value = decode_param_value(msg.param_value, msg.param_type)
                        print(f"DEBUG: Received {param_id}: raw_value={msg.param_value}, type={msg.param_type}, int_value={int_value}")
                        param_values[param_id] = int_value
                if len(param_values) == len(params):
                    break

        print()  # Blank line after debug output

        # Display results
        for param_name in params:
            if param_name in param_values:
                print(f"{param_name:20} = {param_values[param_name]}")
            else:
                print(f"{param_name:20} = <not found>")

    except Exception as e:
        print(f"Error: {e}")


def configure_telem2(port: str, baud: int) -> None:
    """Configure TELEM2 by setting MAV_1_CONFIG = 102 (TELEM 2)."""
    try:
        mav = _connect(port, baud)

        print("Setting MAV_1_CONFIG = 102 (TELEM 2)...")
        # Encode INT32 value for MAVLink transmission
        int_value = 102
        param_value = encode_param_value(int_value, mavutil.mavlink.MAV_PARAM_TYPE_INT32)

        mav.mav.param_set_send(
            mav.target_system,
            mav.target_component,
            b'MAV_1_CONFIG',
            param_value,
            mavutil.mavlink.MAV_PARAM_TYPE_INT32
        )

        msg = mav.recv_match(type='PARAM_VALUE', blocking=True, timeout=PARAMETER_READ_TIMEOUT)
        if msg and msg.param_id == 'MAV_1_CONFIG':
            # Decode the response
            actual_value = decode_param_value(msg.param_value, msg.param_type)
            print(f"  ✓ MAV_1_CONFIG = {actual_value}")

        print("\nSaving to flash...")
        _send_command_long(
            mav,
            mavutil.mavlink.MAV_CMD_PREFLIGHT_STORAGE,
            [1, 0, 0, 0, 0, 0, 0],
            "  ✓ Saved",
            "  ✗ Save failed"
        )

        print("\n✓ TELEM2 configured. Reboot Pixhawk to apply changes.")

    except Exception as e:
        print(f"Error: {e}")
