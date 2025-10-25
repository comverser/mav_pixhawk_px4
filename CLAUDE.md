# Code Style

- Single standard principle: Maintain exactly one way to accomplish each task - avoid creating multiple functions or patterns for the same purpose
- Avoid placeholder defaults: Define default values in one place only (typically at the CLI entry point), not duplicated across multiple function signatures

# Hardware Configuration

## Raspberry Pi 5
- **USB Serial**: `/dev/ttyACM0` at 57600 baud
- **UART**: `/dev/ttyAMA0` (GPIO 14/15)

## Pixhawk
- **Firmware**: PX4 latest
