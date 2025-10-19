"""Scan multiple baud rates to find TELEM2 configuration"""
import serial
import time


def scan_baud_rates(port: str = "/dev/ttyAMA10", duration: float = 3.0) -> None:
    """
    Test multiple baud rates to find which one TELEM2 is using.

    Args:
        port: Serial port (TELEM2)
        duration: Seconds to test each baud rate
    """
    # Common baud rates for MAVLink
    baud_rates = [9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]

    print("="*70)
    print("TELEM2 Baud Rate Scanner")
    print("="*70)
    print(f"Port: {port}")
    print(f"Test duration per rate: {duration}s")
    print("="*70)

    results = {}

    for baud in baud_rates:
        print(f"\nTesting {baud} baud...", end=" ", flush=True)

        try:
            ser = serial.Serial(
                port=port,
                baudrate=baud,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.1
            )

            # Clear buffer
            ser.reset_input_buffer()

            # Read for specified duration
            start_time = time.time()
            total_bytes = 0
            chunks = 0

            while time.time() - start_time < duration:
                data = ser.read(1024)
                if data:
                    total_bytes += len(data)
                    chunks += 1

            ser.close()

            results[baud] = total_bytes

            if total_bytes > 0:
                print(f"✓ {total_bytes} bytes received ({chunks} chunks)")
            else:
                print("✗ No data")

        except Exception as e:
            print(f"✗ Error: {e}")
            results[baud] = 0

    # Summary
    print("\n" + "="*70)
    print("Summary:")
    print("="*70)

    successful = {k: v for k, v in results.items() if v > 0}

    if successful:
        print("\n✓ Data received at these baud rates:")
        for baud, bytes_count in successful.items():
            print(f"  {baud:7d} baud: {bytes_count:6d} bytes")

        # Recommend the one with most data
        best_baud = max(successful.items(), key=lambda x: x[1])
        print(f"\n→ Recommended: {best_baud[0]} baud ({best_baud[1]} bytes)")

    else:
        print("\n⚠ NO DATA at any baud rate!")
        print("\nPossible issues:")
        print("  1. TELEM2 not configured (MAV_1_CONFIG = 102 but MAV_1_RATE = 0)")
        print("  2. Wiring issue:")
        print("     - Verify TX/RX not swapped")
        print("     - Check Pixhawk TELEM2 TX → Pi RX (GPIO 15)")
        print("     - Check Pixhawk TELEM2 RX → Pi TX (GPIO 14)")
        print("     - Ensure grounds connected")
        print("  3. Pi UART not enabled:")
        print("     - Check /boot/config.txt has: enable_uart=1")
        print("     - Check /boot/cmdline.txt doesn't have console=serial0")
        print("  4. Wrong serial port:")
        print(f"     - Current: {port}")
        print("     - Try: /dev/serial0, /dev/ttyS0")

    print("="*70)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scan baud rates for TELEM2")
    parser.add_argument('--port', default='/dev/ttyAMA10', help='Serial port')
    parser.add_argument('--duration', type=float, default=3.0,
                       help='Test duration per baud rate (seconds)')

    args = parser.parse_args()

    scan_baud_rates(args.port, args.duration)
