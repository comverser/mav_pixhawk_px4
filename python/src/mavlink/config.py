"""Pixhawk configuration utilities"""
from pymavlink import mavutil


def reboot(port: str, baud: int) -> None:
    """Reboot Pixhawk."""
    print(f"Connecting to {port} at {baud} baud...")

    try:
        mav = mavutil.mavlink_connection(f"{port},{baud}")
        print("Waiting for heartbeat...")
        mav.wait_heartbeat(timeout=10)
        print(f"Connected to system {mav.target_system}\n")

        print("Rebooting Pixhawk...")
        mav.mav.command_long_send(
            mav.target_system,
            mav.target_component,
            mavutil.mavlink.MAV_CMD_PREFLIGHT_REBOOT_SHUTDOWN,
            0, 1, 0, 0, 0, 0, 0, 0
        )

        msg = mav.recv_match(type='COMMAND_ACK', blocking=True, timeout=5)
        if msg and msg.result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
            print("✓ Reboot command sent")
        else:
            print("✗ Reboot command failed")

    except Exception as e:
        print(f"Error: {e}")


def configure_telem2(port: str, baud: int) -> None:
    """Configure TELEM2 by setting MAV_1_CONFIG = 102 (TELEM 2)."""
    print(f"Connecting to {port} at {baud} baud...")

    try:
        mav = mavutil.mavlink_connection(f"{port},{baud}")
        print("Waiting for heartbeat...")
        mav.wait_heartbeat(timeout=10)
        print(f"Connected to system {mav.target_system}\n")

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
        mav.mav.command_long_send(
            mav.target_system,
            mav.target_component,
            mavutil.mavlink.MAV_CMD_PREFLIGHT_STORAGE,
            0, 1, 0, 0, 0, 0, 0, 0
        )

        msg = mav.recv_match(type='COMMAND_ACK', blocking=True, timeout=5)
        if msg and msg.result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
            print("  ✓ Saved")

        print("\n✓ TELEM2 configured. Reboot Pixhawk to apply changes.")

    except Exception as e:
        print(f"Error: {e}")
