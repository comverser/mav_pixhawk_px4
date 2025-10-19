"""Diagnostic tools for Pixhawk serial connections"""
import serial
import time
import sys


def hex_dump(data: bytes, prefix: str = "") -> None:
    """Print hex dump of data"""
    hex_str = ' '.join(f'{b:02x}' for b in data)
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data)
    print(f"{prefix}{hex_str:48s}  {ascii_str}")


def monitor_raw_serial(port: str, baud: int = 921600, duration: float = 10.0) -> None:
    """
    Monitor raw serial data on a port.

    This bypasses MAVLink parsing to see if ANY data is coming through.
    Useful for diagnosing connection issues.

    Args:
        port: Serial port (e.g., /dev/ttyAMA10)
        baud: Baud rate
        duration: Monitoring duration in seconds
    """
    print(f"Raw Serial Monitor")
    print("=" * 70)
    print(f"Port:     {port}")
    print(f"Baudrate: {baud}")
    print(f"Duration: {duration}s")
    print("=" * 70)
    print()

    try:
        ser = serial.Serial(port, baud, timeout=1)
        print(f"✓ Opened {port} at {baud} baud")
        print(f"  Waiting for data...\n")

        start_time = time.time()
        total_bytes = 0
        chunks = 0

        while time.time() - start_time < duration:
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                total_bytes += len(data)
                chunks += 1

                timestamp = time.time() - start_time
                print(f"[{timestamp:6.2f}s] Received {len(data)} bytes:")

                # Print in 16-byte chunks
                for i in range(0, len(data), 16):
                    chunk = data[i:i+16]
                    hex_dump(chunk, "  ")
                print()
            else:
                time.sleep(0.1)

        print("=" * 70)
        print(f"Summary:")
        print(f"  Total bytes:  {total_bytes}")
        print(f"  Total chunks: {chunks}")

        if total_bytes == 0:
            print()
            print("⚠ NO DATA RECEIVED!")
            print()
            print("Possible issues:")
            print("  1. Pixhawk TELEM2 not sending data")
            print("     → Check MAV_1_CONFIG is set and Pixhawk has been rebooted")
            print("  2. Wiring issue")
            print("     → Verify TX/RX are not swapped")
            print("     → Check Pixhawk TELEM2 TX connects to Pi RX (GPIO 15)")
            print("     → Check Pixhawk TELEM2 RX connects to Pi TX (GPIO 14)")
            print("     → Ensure grounds are connected")
            print("  3. Wrong baud rate")
            print("     → Current: {baud}, expected: 921600")
            print("  4. Wrong serial port")
            print(f"     → Try /dev/serial0 (currently points to {port})")
        elif total_bytes > 0:
            print()
            print("✓ Data is being received!")
            print("  If MAVLink isn't connecting, there may be:")
            print("  - Baud rate mismatch")
            print("  - Corrupted data (check wiring quality)")
            print("  - Wrong MAVLink version")

        ser.close()

    except serial.SerialException as e:
        print(f"✗ Error opening port: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


def test_loopback(port: str, baud: int = 921600) -> None:
    """
    Test serial port by sending data and checking if it comes back.

    NOTE: This requires TX and RX to be physically connected (loopback).
    Disconnect from Pixhawk before running this test!

    Args:
        port: Serial port
        baud: Baud rate
    """
    print(f"Serial Loopback Test")
    print("=" * 70)
    print(f"⚠ WARNING: This test requires TX and RX to be physically connected!")
    print(f"           Disconnect from Pixhawk first!")
    print("=" * 70)
    print()
    input("Press Enter to continue or Ctrl+C to cancel...")
    print()

    try:
        ser = serial.Serial(port, baud, timeout=1)
        print(f"✓ Opened {port} at {baud} baud")

        test_data = b"LOOPBACK_TEST_123"
        print(f"\nSending: {test_data}")

        # Clear any existing data
        ser.reset_input_buffer()

        # Send test data
        ser.write(test_data)
        ser.flush()
        time.sleep(0.1)

        # Try to receive
        received = ser.read(len(test_data))

        print(f"Received: {received}")

        if received == test_data:
            print("\n✓ LOOPBACK TEST PASSED!")
            print("  The serial port hardware is working correctly.")
        elif len(received) == 0:
            print("\n✗ LOOPBACK TEST FAILED!")
            print("  No data received. Possible issues:")
            print("  - TX and RX not connected (did you create the loopback?)")
            print("  - Serial port not working")
        else:
            print("\n⚠ LOOPBACK TEST PARTIAL!")
            print("  Received data but it doesn't match.")
            print("  Possible issues:")
            print("  - Data corruption")
            print("  - Baud rate issue")

        ser.close()

    except serial.SerialException as e:
        print(f"✗ Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nTest cancelled")
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Serial port diagnostics")
    subparsers = parser.add_subparsers(dest='command', help='Diagnostic command')

    # Raw monitor
    monitor_parser = subparsers.add_parser('monitor', help='Monitor raw serial data')
    monitor_parser.add_argument('port', help='Serial port (e.g., /dev/ttyAMA10)')
    monitor_parser.add_argument('--baud', type=int, default=921600, help='Baud rate')
    monitor_parser.add_argument('--duration', type=float, default=10.0, help='Duration in seconds')

    # Loopback test
    loopback_parser = subparsers.add_parser('loopback', help='Test serial port with loopback')
    loopback_parser.add_argument('port', help='Serial port')
    loopback_parser.add_argument('--baud', type=int, default=921600, help='Baud rate')

    args = parser.parse_args()

    if args.command == 'monitor':
        monitor_raw_serial(args.port, args.baud, args.duration)
    elif args.command == 'loopback':
        test_loopback(args.port, args.baud)
    else:
        parser.print_help()
