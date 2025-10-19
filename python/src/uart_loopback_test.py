"""Test UART loopback - connect TX to RX physically to test"""
import serial
import time


def test_uart_loopback(port: str = "/dev/ttyAMA10", baud: int = 921600, skip_prompt: bool = False) -> None:
    """
    Test UART by sending data and trying to receive it back.

    HARDWARE SETUP REQUIRED:
    - Physically connect GPIO 14 (TX) to GPIO 15 (RX) with a jumper wire
    - Remove the Pixhawk connection temporarily
    """
    print("="*70)
    print("UART Loopback Test")
    print("="*70)
    print(f"Port: {port}")
    print(f"Baud: {baud}")
    print()
    print("SETUP: Physically connect TX to RX:")
    print("  - GPIO 14 (TX, pin 8)  →  GPIO 15 (RX, pin 10)")
    print("  - Disconnect Pixhawk TELEM2 temporarily")
    print()
    if not skip_prompt:
        input("Press Enter when ready...")
    print()

    try:
        ser = serial.Serial(
            port=port,
            baudrate=baud,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1
        )

        test_message = b"UART_TEST_123"

        print(f"Sending: {test_message}")
        ser.write(test_message)
        ser.flush()

        time.sleep(0.1)

        received = ser.read(100)

        if received == test_message:
            print(f"✓ Received: {received}")
            print()
            print("="*70)
            print("✓ UART HARDWARE IS WORKING!")
            print("="*70)
            print()
            print("This means:")
            print("  - Pi UART is configured correctly")
            print("  - TX/RX pins are functional")
            print("  - The issue is likely:")
            print("    • Pixhawk TELEM2 wiring")
            print("    • TX/RX swapped on Pixhawk side")
            print("    • Pixhawk TELEM2 not actually transmitting")
        elif received:
            print(f"⚠ Received (DIFFERENT): {received}")
            print("  Possible baud rate mismatch in loopback")
        else:
            print("✗ Nothing received")
            print()
            print("="*70)
            print("⚠ UART ISSUE DETECTED")
            print("="*70)
            print()
            print("Possible problems:")
            print("  1. UART not enabled - check /boot/firmware/config.txt")
            print("  2. TX/RX not actually connected")
            print("  3. Wrong GPIO pins")

        ser.close()

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_uart_loopback()
