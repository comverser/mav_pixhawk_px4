"""Pixhawk configuration utilities"""
from pymavlink import mavutil
import time
import os


def _connect(port: str, baud: int):
    """Connect to Pixhawk and wait for heartbeat."""
    print(f"Connecting to {port} at {baud} baud...")
    mav = mavutil.mavlink_connection(f"{port},{baud}")
    print("Waiting for heartbeat...")
    mav.wait_heartbeat(timeout=10)
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
    msg = mav.recv_match(type='COMMAND_ACK', blocking=True, timeout=5)
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

        print("Waiting for Pixhawk to boot (15s)...", end="", flush=True)
        for _ in range(15):
            time.sleep(1)
            print(".", end="", flush=True)
        print()

        print("\nWaiting for device to reappear...", end="", flush=True)
        device_found = False
        for _ in range(15):
            if os.path.exists(port):
                print(" ✓ Device found")
                device_found = True
                break
            print(".", end="", flush=True)
            time.sleep(1)

        if not device_found:
            print(f" ✗ Device {port} did not reappear")
            return

        print("Reconnecting...", end="", flush=True)
        for attempt in range(5):
            try:
                time.sleep(1)
                mav = mavutil.mavlink_connection(f"{port},{baud}")
                msg = mav.wait_heartbeat(timeout=10)
                if msg:
                    print(" ✓")
                    print(f"✓ Pixhawk rebooted successfully!")
                    print(f"  System ID: {mav.target_system}")
                    return
            except Exception:
                print(".", end="", flush=True)

        print(" ✗")
        print("✗ Failed to reconnect after reboot")

    except Exception as e:
        print(f"Error: {e}")


def configure_telem2(port: str, baud: int) -> None:
    """Configure TELEM2 by setting MAV_1_CONFIG = 102 (TELEM 2)."""
    try:
        mav = _connect(port, baud)

        # Only set MAV_1_CONFIG - PX4 auto-configures other params after reboot
        print("Setting MAV_1_CONFIG = 102 (TELEM 2)...")
        mav.mav.param_set_send(
            mav.target_system,
            mav.target_component,
            b'MAV_1_CONFIG',
            102,
            mavutil.mavlink.MAV_PARAM_TYPE_INT32
        )

        msg = mav.recv_match(type='PARAM_VALUE', blocking=True, timeout=3)
        if msg and msg.param_id == 'MAV_1_CONFIG':
            print(f"  ✓ MAV_1_CONFIG = {int(msg.param_value)}")

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
