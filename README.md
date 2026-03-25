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

#### UART Setup

Enable UART on GPIO 14/15 by adding the following to `/boot/firmware/config.txt`:

```
dtoverlay=uart0-pi5
```

Reboot to apply. This creates `/dev/ttyAMA0` for TELEM2 connections.

Set up UART permissions:

```bash
sudo usermod -aG dialout $USER
sudo bash -c 'echo "KERNEL==\"ttyAMA0\", GROUP=\"dialout\", MODE=\"0660\"" > /etc/udev/rules.d/99-ttyAMA0.rules'
sudo udevadm control --reload-rules && sudo udevadm trigger
```

Log out and back in (or run `newgrp dialout`) for the group change to take effect.

#### Disable Serial Console

The serial console and login shell on ttyAMA0 must be disabled when using UART for Pixhawk communication. MAVLink binary data gets interpreted as SysRq key commands, which can trigger instant reboots, emergency filesystem remounts, and other destructive kernel actions.

Via `raspi-config` (recommended):

```bash
sudo raspi-config
# Interface Options → Serial Port
#   Login shell over serial: No
#   Serial port hardware enabled: Yes
```

Or manually:

```bash
sudo sed -i 's/console=serial0,115200 //' /boot/firmware/cmdline.txt
```

The `serial-getty@ttyAMA0.service` is auto-generated from the `console=` kernel parameter, so removing it from cmdline.txt also eliminates the login shell.

Reboot to apply.

#### Persistent Journal

Raspberry Pi OS defaults to volatile journal storage (RAM only), so all logs are lost on unexpected shutdown. Enable persistent journal to preserve logs across reboots:

```bash
sudo mkdir -p /var/log/journal/$(cat /etc/machine-id)
sudo mkdir -p /etc/systemd/journald.conf.d
echo -e "[Journal]\nStorage=persistent" | sudo tee /etc/systemd/journald.conf.d/50-persistent.conf
sudo systemctl restart systemd-journald
sudo journalctl --flush
```

This overrides the RPi drop-in at `/usr/lib/systemd/journald.conf.d/40-rpi-volatile-storage.conf` that forces `Storage=volatile`.

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
