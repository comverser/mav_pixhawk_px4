# Code Style

- Single standard principle: Maintain exactly one way to accomplish each task - avoid creating multiple functions or patterns for the same purpose
- Avoid placeholder defaults: Define default values in one place only (typically at the CLI entry point), not duplicated across multiple function signatures
- MAVLink/MAVSDK independence: Keep `mavlink/` and `mavsdk/` directories completely independent - never mix or import between them (applies to all languages)
- Direct imports only: Use explicit imports directly from source modules - no re-export aggregation (no `__all__` in Python, no re-exports in Rust mod.rs)

# Hardware Configuration

## Raspberry Pi 5
- **USB Serial**: `/dev/ttyACM0` at 57600 baud
- **UART**: `/dev/ttyAMA0` (GPIO 14/15)

## Pixhawk
- **Firmware**: PX4 latest
