"""Pixhawk configuration utilities"""
from pymavlink import mavutil
import time


def check_telem2_config(port: str = "/dev/ttyACM0", baud: int = 57600) -> None:
    """
    Check TELEM2 port configuration on Pixhawk.

    Connects via USB and queries parameters that control TELEM2 output.

    PX4 parameters:
        MAV_1_CONFIG - Serial port assignment (102 = TELEM2)
        MAV_1_RATE - Baudrate in bytes/second
        MAV_1_MODE - MAVLink mode (0=Normal, 1=Custom, 2=Onboard, 4=External Vision)

    ArduPilot parameters:
        SERIAL2_PROTOCOL - Protocol (1=MAVLink1, 2=MAVLink2)
        SERIAL2_BAUD - Baudrate (57=57600, 921=921600)
    """
    print(f"\nConnecting to Pixhawk via {port} at {baud} baud...")

    try:
        mav = mavutil.mavlink_connection(f"{port},{baud}")
        print("Waiting for heartbeat...")
        mav.wait_heartbeat(timeout=10)
        print(f"Connected to system {mav.target_system}\n")

        # Request specific TELEM2 parameters
        print("Requesting TELEM2 parameters...")

        params = {}
        telem2_params = [
            "MAV_1_CONFIG", "MAV_1_RATE", "MAV_1_MODE",  # PX4
            "SERIAL2_PROTOCOL", "SERIAL2_BAUD"             # ArduPilot
        ]

        # Request each parameter individually
        for param_name in telem2_params:
            mav.mav.param_request_read_send(
                mav.target_system,
                mav.target_component,
                param_name.encode('utf-8'),
                -1
            )

        # Collect responses
        start_time = time.time()
        while time.time() - start_time < 3:
            msg = mav.recv_match(type='PARAM_VALUE', blocking=True, timeout=0.5)
            if msg:
                param_id = msg.param_id
                if param_id in telem2_params:
                    params[param_id] = msg.param_value

        # Display results
        print("\n" + "="*60)
        print("TELEM2 Configuration")
        print("="*60)

        if "MAV_1_CONFIG" in params:
            # PX4 autopilot
            print("\nAutopilot: PX4")
            print(f"MAV_1_CONFIG:  {int(params['MAV_1_CONFIG'])}")
            if int(params['MAV_1_CONFIG']) == 102:
                print("               ✓ Configured for TELEM2 port")
            elif int(params['MAV_1_CONFIG']) == 0:
                print("               ✗ DISABLED - TELEM2 not configured!")
            else:
                print(f"               ⚠ Configured for different port")

            if "MAV_1_RATE" in params:
                rate = int(params['MAV_1_RATE'])
                print(f"MAV_1_RATE:    {rate} B/s")
                # Common rates: 1200 B/s ≈ 9600 baud, 5760 B/s ≈ 57600 baud
                estimated_baud = rate * 10
                print(f"               (≈{estimated_baud} baud)")
            else:
                print("MAV_1_RATE:    (not retrieved)")
                print("               ⚠ Parameter not found - may need reboot")

            if "MAV_1_MODE" in params:
                mode = int(params['MAV_1_MODE'])
                modes = {0: "Normal", 1: "Custom", 2: "Onboard", 4: "Ext Vision"}
                print(f"MAV_1_MODE:    {mode} ({modes.get(mode, 'Unknown')})")
            else:
                print("MAV_1_MODE:    (not retrieved)")

        elif "SERIAL2_PROTOCOL" in params:
            # ArduPilot
            print("\nAutopilot: ArduPilot")
            protocol = int(params['SERIAL2_PROTOCOL'])
            print(f"SERIAL2_PROTOCOL: {protocol}")
            if protocol in [1, 2]:
                print(f"                  ✓ MAVLink{protocol} enabled")
            elif protocol == 0:
                print("                  ✗ DISABLED - TELEM2 not configured!")
            else:
                print("                  ⚠ Different protocol")

            if "SERIAL2_BAUD" in params:
                baud_code = int(params['SERIAL2_BAUD'])
                baud_map = {1: 1200, 2: 2400, 4: 4800, 9: 9600, 19: 19200,
                           38: 38400, 57: 57600, 111: 111100, 115: 115200,
                           230: 230400, 256: 256000, 460: 460800, 500: 500000,
                           921: 921600, 1500: 1500000}
                actual_baud = baud_map.get(baud_code, baud_code)
                print(f"SERIAL2_BAUD:     {baud_code} ({actual_baud} baud)")
        else:
            print("\n⚠ Could not retrieve TELEM2 parameters")
            print("Parameters may be named differently on this autopilot")

        print("="*60)

    except Exception as e:
        print(f"Error: {e}")


def configure_telem2(port: str = "/dev/ttyACM0", baud: int = 57600,
                     target_baudrate: int = 921600) -> None:
    """
    Configure TELEM2 port on PX4 autopilot.

    Args:
        port: USB port to connect to Pixhawk
        baud: Current baudrate of USB port
        target_baudrate: Desired baudrate for TELEM2 (default: 921600)
    """
    print(f"\nConfiguring TELEM2 for {target_baudrate} baud...")
    print(f"Connecting via {port} at {baud} baud...\n")

    try:
        mav = mavutil.mavlink_connection(f"{port},{baud}")
        print("Waiting for heartbeat...")
        mav.wait_heartbeat(timeout=10)
        print(f"Connected to system {mav.target_system}\n")

        # Set MAV_1_CONFIG to 102 (TELEM2)
        print("Setting MAV_1_CONFIG = 102 (TELEM2)...")
        mav.mav.param_set_send(
            mav.target_system,
            mav.target_component,
            b'MAV_1_CONFIG',
            102,
            mavutil.mavlink.MAV_PARAM_TYPE_INT32
        )

        # Wait for acknowledgment
        msg = mav.recv_match(type='PARAM_VALUE', blocking=True, timeout=3)
        if msg and msg.param_id == 'MAV_1_CONFIG':
            print(f"  ✓ MAV_1_CONFIG = {int(msg.param_value)}")

        # Set baudrate: MAV_1_RATE is in bytes/second
        # For serial communication: bytes/sec ≈ baudrate / 10
        rate = target_baudrate // 10
        print(f"Setting MAV_1_RATE = {rate} B/s (~{target_baudrate} baud)...")
        mav.mav.param_set_send(
            mav.target_system,
            mav.target_component,
            b'MAV_1_RATE',
            rate,
            mavutil.mavlink.MAV_PARAM_TYPE_INT32
        )

        # Wait for acknowledgment
        msg = mav.recv_match(type='PARAM_VALUE', blocking=True, timeout=3)
        if msg and msg.param_id == 'MAV_1_RATE':
            print(f"  ✓ MAV_1_RATE = {int(msg.param_value)} B/s")
        else:
            print("  ⚠ MAV_1_RATE may not exist on this firmware version")

        # Try to set MAV_1_MODE (Normal mode)
        print(f"Setting MAV_1_MODE = 0 (Normal mode)...")
        mav.mav.param_set_send(
            mav.target_system,
            mav.target_component,
            b'MAV_1_MODE',
            0,
            mavutil.mavlink.MAV_PARAM_TYPE_INT32
        )

        # Wait for acknowledgment
        msg = mav.recv_match(type='PARAM_VALUE', blocking=True, timeout=3)
        if msg and msg.param_id == 'MAV_1_MODE':
            print(f"  ✓ MAV_1_MODE = {int(msg.param_value)}")
        else:
            print("  ⚠ MAV_1_MODE may not exist on this firmware version")

        # Save parameters to EEPROM/flash
        print("\nSaving parameters to flash...")
        mav.mav.command_long_send(
            mav.target_system,
            mav.target_component,
            mavutil.mavlink.MAV_CMD_PREFLIGHT_STORAGE,
            0,  # confirmation
            1,  # param1: 1 = save parameters
            0, 0, 0, 0, 0, 0  # unused params
        )

        # Wait for save acknowledgment
        msg = mav.recv_match(type='COMMAND_ACK', blocking=True, timeout=5)
        if msg and msg.result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
            print("  ✓ Parameters saved to flash")
        else:
            print("  ⚠ Parameter save acknowledgment not received")

        print("\n" + "="*60)
        print("✓ TELEM2 configured successfully!")
        print("="*60)
        print("\nNOTE: You must REBOOT the Pixhawk for changes to take effect.")
        print("      Disconnect power, wait 5 seconds, then reconnect.\n")

    except Exception as e:
        print(f"Error: {e}")


def reboot_pixhawk(port: str = "/dev/ttyACM0", baud: int = 57600) -> None:
    """
    Reboot the Pixhawk autopilot via MAVLink command.

    Args:
        port: Serial port to connect to Pixhawk
        baud: Baudrate for connection
    """
    print(f"\nRebooting Pixhawk via {port} at {baud} baud...")

    try:
        mav = mavutil.mavlink_connection(f"{port},{baud}")
        print("Waiting for heartbeat...")
        mav.wait_heartbeat(timeout=10)
        print(f"Connected to system {mav.target_system}\n")

        # Send reboot command
        # MAV_CMD_PREFLIGHT_REBOOT_SHUTDOWN = 246
        # param1 = 1: Reboot autopilot
        print("Sending reboot command...")
        mav.mav.command_long_send(
            mav.target_system,
            mav.target_component,
            mavutil.mavlink.MAV_CMD_PREFLIGHT_REBOOT_SHUTDOWN,
            0,  # confirmation
            1,  # param1: 1 = reboot autopilot
            0,  # param2: 0 = reserved
            0,  # param3: 0 = reserved
            0,  # param4: 0 = reserved
            0,  # param5: 0 = reserved
            0,  # param6: 0 = reserved
            0   # param7: 0 = reserved
        )

        # Wait for acknowledgment
        print("Waiting for acknowledgment...")
        msg = mav.recv_match(type='COMMAND_ACK', blocking=True, timeout=3)

        if msg:
            if msg.result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
                print("\n✓ Reboot command accepted")
                print("  Pixhawk is rebooting...")
                print("  Wait ~5 seconds for reboot to complete.\n")
            else:
                print(f"\n⚠ Reboot command result: {msg.result}")
        else:
            print("\n⚠ No acknowledgment received (Pixhawk may still be rebooting)")

    except Exception as e:
        print(f"Error: {e}")
