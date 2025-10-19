"""Configure MAV_0 (instance 0) for TELEM2"""
from pymavlink import mavutil
import time


def configure_mav0_telem2(port: str = "/dev/ttyACM0", baud: int = 57600,
                          target_baudrate: int = 921600) -> None:
    """
    Configure MAV_0 (MAVLink instance 0) for TELEM2.

    This firmware only supports MAV_0_RATE/MAV_0_MODE, not MAV_1_*.
    """
    print("\n" + "="*70)
    print("Configuring MAV_0 for TELEM2")
    print("="*70)
    print(f"Connecting via {port} at {baud} baud...\n")

    try:
        mav = mavutil.mavlink_connection(f"{port},{baud}")
        print("Waiting for heartbeat...")
        mav.wait_heartbeat(timeout=10)
        print(f"Connected to system {mav.target_system}\n")

        # Set MAV_0_CONFIG to 102 (TELEM2)
        print("Setting MAV_0_CONFIG = 102 (TELEM2)...")
        mav.mav.param_set_send(
            mav.target_system,
            mav.target_component,
            b'MAV_0_CONFIG',
            102,
            mavutil.mavlink.MAV_PARAM_TYPE_INT32
        )
        time.sleep(0.5)

        # Set baudrate
        rate = target_baudrate // 10
        print(f"Setting MAV_0_RATE = {rate} B/s (~{target_baudrate} baud)...")
        mav.mav.param_set_send(
            mav.target_system,
            mav.target_component,
            b'MAV_0_RATE',
            rate,
            mavutil.mavlink.MAV_PARAM_TYPE_INT32
        )
        time.sleep(0.5)

        # Set mode to Normal (0)
        print(f"Setting MAV_0_MODE = 0 (Normal)...")
        mav.mav.param_set_send(
            mav.target_system,
            mav.target_component,
            b'MAV_0_MODE',
            0,
            mavutil.mavlink.MAV_PARAM_TYPE_INT32
        )
        time.sleep(0.5)

        # Disable MAV_1_CONFIG
        print("Setting MAV_1_CONFIG = 0 (Disabled)...")
        mav.mav.param_set_send(
            mav.target_system,
            mav.target_component,
            b'MAV_1_CONFIG',
            0,
            mavutil.mavlink.MAV_PARAM_TYPE_INT32
        )
        time.sleep(0.5)

        # Save parameters
        print("\nSaving parameters to flash...")
        mav.mav.command_long_send(
            mav.target_system,
            mav.target_component,
            mavutil.mavlink.MAV_CMD_PREFLIGHT_STORAGE,
            0,  # confirmation
            1,  # param1: 1 = save parameters
            0, 0, 0, 0, 0, 0
        )

        msg = mav.recv_match(type='COMMAND_ACK', blocking=True, timeout=5)
        if msg and msg.result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
            print("  ✓ Parameters saved to flash")
        else:
            print("  ⚠ Save acknowledgment not received (may still work)")

        print("\n" + "="*70)
        print("✓ MAV_0 configured for TELEM2!")
        print("="*70)
        print("\nConfiguration:")
        print(f"  MAV_0_CONFIG = 102 (TELEM2)")
        print(f"  MAV_0_RATE   = {rate} B/s (~{target_baudrate} baud)")
        print(f"  MAV_0_MODE   = 0 (Normal)")
        print(f"  MAV_1_CONFIG = 0 (Disabled)")
        print("\nNOTE: You must REBOOT the Pixhawk for changes to take effect!")
        print("="*70)

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Configure MAV_0 for TELEM2")
    parser.add_argument('--port', default='/dev/ttyACM0', help='USB port')
    parser.add_argument('--usb-baud', type=int, default=57600, help='USB baud rate')
    parser.add_argument('--telem-baud', type=int, default=921600, help='TELEM2 baud rate')
    args = parser.parse_args()

    configure_mav0_telem2(args.port, args.usb_baud, args.telem_baud)
