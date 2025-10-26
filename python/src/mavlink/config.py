"""Pixhawk configuration utilities"""
from pymavlink import mavutil
import time
import os
import glob
from typing import Dict, List, Tuple

from src.common.constants import (
    HEARTBEAT_TIMEOUT,
    COMMAND_ACK_TIMEOUT,
    PARAMETER_READ_TIMEOUT,
    REBOOT_WAIT_SECONDS,
    DEVICE_POLL_ATTEMPTS,
    RECONNECT_ATTEMPTS,
)
from src.mavlink.parameters import encode_param_value, decode_param_value
from src.mavlink import connection

# ============================================================================
# Constants
# ============================================================================

# Parameters that are auto-set by hardware detection/calibration
AUTO_CALIBRATION_PATTERNS = [
    '_ID',      # Sensor hardware IDs
    '_PRIO',    # Sensor priorities
    'CAL_GYRO', # Gyro calibration offsets
    'CAL_ACC',  # Accelerometer calibration
    'CAL_MAG',  # Magnetometer calibration
]

# Parameter comparison tolerance for floating point values
FLOAT_COMPARISON_TOLERANCE = 1e-6

# MAVLink integer parameter types
INT_PARAM_TYPES = [1, 2, 3, 4, 5, 6]  # INT8, UINT8, INT16, UINT16, INT32, UINT32


# ============================================================================
# Connection Helpers
# ============================================================================
# Note: Connection logic centralized in src.mavlink.connection module

def _handle_error(e: Exception, show_traceback: bool = False):
    """Standardized error handling for configuration commands.

    Args:
        e: The exception to handle
        show_traceback: Whether to show full traceback (for debugging)
    """
    print(f"Error: {e}")
    if show_traceback:
        import traceback
        print("\nFull error details:")
        traceback.print_exc()
        print("\nTip: Try unplugging and replugging the Pixhawk, or check if another program is using the serial port")


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


# ============================================================================
# Parameter Loading & Reading
# ============================================================================

def _load_reference_params(reference_file: str) -> Dict[str, Dict]:
    """Load reference parameters from file.

    Args:
        reference_file: Path to reference params file

    Returns:
        Dict mapping parameter names to {'value': value, 'type': type}
    """
    reference_params = {}
    with open(reference_file, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            # Parse parameter line: Vehicle-Id Component-Id Name Value Type
            parts = line.split('\t')
            if len(parts) >= 5:
                param_name = parts[2]
                param_type = int(parts[4])
                # Parse value based on type
                if param_type in INT_PARAM_TYPES:
                    param_value = int(parts[3])
                else:  # Float types (REAL32)
                    param_value = float(parts[3])
                reference_params[param_name] = {
                    'value': param_value,
                    'type': param_type
                }
    return reference_params


def _read_all_params(mav) -> Dict[str, Dict]:
    """Read all parameters from connected Pixhawk.

    Args:
        mav: Connected MAVLink connection

    Returns:
        Dict mapping parameter names to {'value': value, 'type': type}
    """
    print("Requesting all parameters from Pixhawk...")
    mav.mav.param_request_list_send(mav.target_system, mav.target_component)

    current_params = {}
    print("Reading parameters...", end="", flush=True)

    # Collect all PARAM_VALUE messages
    timeout = time.time() + 15
    last_msg_time = time.time()
    expected_count = None

    while time.time() < timeout:
        msg = mav.recv_match(type='PARAM_VALUE', blocking=False, timeout=0.5)
        if msg:
            last_msg_time = time.time()
            param_id = msg.param_id.decode('utf-8') if isinstance(msg.param_id, bytes) else msg.param_id
            param_id = param_id.rstrip('\x00')
            current_params[param_id] = {
                'value': msg.param_value,
                'type': msg.param_type
            }
            # Show progress
            if len(current_params) % 50 == 0:
                print(".", end="", flush=True)

            # Track expected count
            if expected_count is None:
                expected_count = msg.param_count

            # Check if we've received all params
            if msg.param_index + 1 == msg.param_count:
                break

        # Break if no messages received for 3 seconds
        if time.time() - last_msg_time > 3:
            break

    print(f" ✓ Read {len(current_params)} parameters\n")
    return current_params


# ============================================================================
# Parameter Comparison
# ============================================================================

def _is_auto_calibration_param(name: str) -> bool:
    """Check if parameter is auto-set by calibration/hardware detection."""
    return any(pattern in name for pattern in AUTO_CALIBRATION_PATTERNS)


def _compare_parameters(reference_params: Dict[str, Dict], current_params: Dict[str, Dict]) -> Tuple[int, List[Dict], List[Dict]]:
    """Compare reference and current parameters.

    Args:
        reference_params: Reference parameter dict
        current_params: Current parameter dict from Pixhawk

    Returns:
        Tuple of (matching_count, config_differences, auto_cal_differences)
    """
    matching = 0
    config_differences = []
    auto_cal_differences = []

    for param_name in reference_params:
        if param_name not in current_params:
            continue

        ref_val = reference_params[param_name]['value']
        cur_val_raw = current_params[param_name]['value']
        ref_type = reference_params[param_name]['type']
        cur_type = current_params[param_name]['type']

        # Decode current value from MAVLink float representation
        if cur_type in INT_PARAM_TYPES:
            cur_val = decode_param_value(cur_val_raw, cur_type)
        else:  # REAL32
            cur_val = cur_val_raw

        # Compare values
        values_match = False
        if ref_type in INT_PARAM_TYPES:
            values_match = (ref_val == cur_val and ref_type == cur_type)
        else:  # REAL32
            values_match = (abs(ref_val - cur_val) < FLOAT_COMPARISON_TOLERANCE and ref_type == cur_type)

        if values_match:
            matching += 1
        else:
            diff_entry = {
                'name': param_name,
                'reference': ref_val,
                'current': cur_val,
                'ref_type': ref_type,
                'cur_type': cur_type
            }
            # Categorize the difference
            if _is_auto_calibration_param(param_name):
                auto_cal_differences.append(diff_entry)
            else:
                config_differences.append(diff_entry)

    return matching, config_differences, auto_cal_differences


# ============================================================================
# Result Display
# ============================================================================

def _display_comparison_results(
    matching: int,
    config_differences: List[Dict],
    auto_cal_differences: List[Dict],
    only_in_reference: int,
    only_in_current: int
):
    """Display parameter comparison results.

    Args:
        matching: Number of matching parameters
        config_differences: List of configuration differences
        auto_cal_differences: List of auto-calibration differences
        only_in_reference: Count of parameters only in reference
        only_in_current: Count of parameters only in current
    """
    print("=" * 80)
    print("PARAMETER COMPARISON RESULTS")
    print("=" * 80)
    print(f"Matching parameters:              {matching}")
    print(f"Configuration differences:        {len(config_differences)}")
    print(f"Auto-calibration differences:     {len(auto_cal_differences)}")
    print(f"Only in reference:                {only_in_reference}")
    print(f"Only in current:                  {only_in_current}")
    print("=" * 80)

    if len(config_differences) > 0:
        print(f"\nCONFIGURATION DIFFERENCES (user-modified, showing up to 20):")
        print("-" * 80)
        for i, diff in enumerate(config_differences[:20]):
            print(f"{diff['name']:25} | Ref: {diff['reference']:20} | Cur: {diff['current']:20}")
        if len(config_differences) > 20:
            print(f"... and {len(config_differences) - 20} more configuration differences")

    if len(auto_cal_differences) > 0:
        print(f"\nAUTO-CALIBRATION DIFFERENCES (hardware detection, showing up to 10):")
        print("-" * 80)
        for i, diff in enumerate(auto_cal_differences[:10]):
            print(f"{diff['name']:25} | Ref: {diff['reference']:20} | Cur: {diff['current']:20}")
        if len(auto_cal_differences) > 10:
            print(f"... and {len(auto_cal_differences) - 10} more auto-calibration differences")

    # Verdict
    print("\n" + "=" * 80)
    if len(config_differences) == 0 and len(auto_cal_differences) == 0:
        print("✓ VERDICT: Perfect match - device is at firmware defaults!")
    elif len(config_differences) == 0:
        print(f"✓ VERDICT: Device is at firmware defaults!")
        print(f"  ({len(auto_cal_differences)} auto-calibration differences are expected from hardware detection)")
    elif len(config_differences) < 5:
        print(f"⚠ VERDICT: Mostly at defaults with {len(config_differences)} configuration change(s)")
        if len(auto_cal_differences) > 0:
            print(f"  (Plus {len(auto_cal_differences)} auto-calibration differences)")
    else:
        print(f"✗ VERDICT: Significant configuration differences ({len(config_differences)} changes)")
        if len(auto_cal_differences) > 0:
            print(f"  (Plus {len(auto_cal_differences)} auto-calibration differences)")
    print("=" * 80)


# ============================================================================
# Configuration Commands
# ============================================================================


def reset_params(port: str, baud: int) -> None:
    """Reset all parameters to factory defaults."""
    try:
        mav = connection.connect(connection.make_serial_address(port, baud))

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
        _handle_error(e)


def reboot(port: str, baud: int) -> None:
    """Reboot Pixhawk and verify it comes back online."""
    try:
        mav = connection.connect(connection.make_serial_address(port, baud))

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

        # Reconnect using the stabilized connection helper
        print("Reconnecting...")
        try:
            mav = connection.connect(connection.make_serial_address(new_port, baud))
            print(f"✓ Pixhawk rebooted successfully!")
            print(f"  System ID: {mav.target_system}")
            if new_port != port:
                print(f"  Device path changed: {port} → {new_port}")
        except TimeoutError:
            print("✗ Failed to reconnect after reboot")

    except Exception as e:
        _handle_error(e)


def compare_params_with_defaults(port: str, baud: int, reference_file: str = None) -> None:
    """Compare current Pixhawk parameters with reference defaults to verify reset.

    Args:
        port: Serial port path
        baud: Baud rate
        reference_file: Path to reference params file. If None, uses px4_v1.16.0_default.params from project root.
    """
    try:
        # Connect to Pixhawk
        mav = connection.connect(connection.make_serial_address(port, baud))

        # Determine reference file path
        if reference_file is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            reference_file = os.path.join(script_dir, '..', '..', '..', 'px4_v1.16.0_default.params')

        # Load reference parameters
        print(f"Loading reference parameters from {reference_file}...")
        reference_params = _load_reference_params(reference_file)
        print(f"✓ Loaded {len(reference_params)} reference parameters\n")

        # Read current parameters from Pixhawk
        current_params = _read_all_params(mav)

        # Compare parameters
        matching, config_diffs, auto_cal_diffs = _compare_parameters(reference_params, current_params)

        # Count parameters only in reference or only in current
        only_in_reference = sum(1 for p in reference_params if p not in current_params)
        only_in_current = sum(1 for p in current_params if p not in reference_params)

        # Display results
        _display_comparison_results(matching, config_diffs, auto_cal_diffs, only_in_reference, only_in_current)

    except FileNotFoundError as e:
        print(f"Error: Reference file not found: {reference_file}")
    except TimeoutError as e:
        _handle_error(e)
        print("Tip: Make sure the Pixhawk is powered on and connected to the correct port")
    except Exception as e:
        _handle_error(e, show_traceback=True)


def configure_telem2(port: str, baud: int) -> None:
    """Configure TELEM2 by setting MAV_1_CONFIG = 102 (TELEM 2)."""
    try:
        mav = connection.connect(connection.make_serial_address(port, baud))

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
        _handle_error(e)
