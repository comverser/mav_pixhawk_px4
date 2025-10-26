# mav_pixhawk_px4

Multi-language MAVLink implementations for drone control and telemetry.

## Architecture

- **mavlink/**: Direct MAVLink protocol implementation
- **mavsdk/**: MAVSDK library implementation
- These directories must remain completely independent (applies to all languages)

## Prerequisites

- [just](https://github.com/casey/just) - Command runner
- [PX4 SITL](https://github.com/comverser/px4_with_extern_modules) - Only for UDP/SITL connections

## Hardware Configuration

### Raspberry Pi 5
- **USB Serial**: `/dev/ttyACM0` at 57600 baud
- **UART**: `/dev/ttyAMA0` (GPIO 14/15)

### Pixhawk
- **Firmware**: PX4 latest

## Quick Start

```bash
just
```

## Languages

- Python
- C++
- Rust
