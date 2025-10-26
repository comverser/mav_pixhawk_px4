"""CLI entry point"""
import asyncio
import sys
from typing import Callable, Any

from src.mavsdk.commands import flight, shell, offboard
from src.mavsdk.telemetry import ekf
from src.mavlink.telemetry import rc_channels, heartbeat
from src.mavlink import config
from src.common.constants import DEFAULT_USB_PORT, DEFAULT_USB_BAUD


def _parse_serial_args(args: list[str], start_idx: int = 1) -> tuple[str, int]:
    """Parse serial port and baud rate from args."""
    port = args[start_idx] if len(args) > start_idx else DEFAULT_USB_PORT
    baud = int(args[start_idx + 1]) if len(args) > start_idx + 1 else DEFAULT_USB_BAUD
    return port, baud


def _parse_duration_arg(args: list[str], start_idx: int = 1, default: float = 10.0) -> float:
    """Parse duration argument from args."""
    return float(args[start_idx]) if len(args) > start_idx else default


# Command registry: maps command names to handler functions
COMMAND_HANDLERS: dict[str, Callable[[list[str]], Any]] = {
    # Flight commands (async)
    "takeoff": lambda args: asyncio.run(flight.takeoff()),
    "shell": lambda args: asyncio.run(shell.execute(' '.join(args[1:]))),
    "offboard-hover": lambda args: asyncio.run(offboard.test_hover()),
    "offboard": lambda args: asyncio.run(offboard.offboard_control(
        float(args[1]), float(args[2]), float(args[3]), float(args[4]),
        float(args[5]) if len(args) > 5 else 10.0
    )),

    # Telemetry commands (async)
    "ekf-status": lambda args: asyncio.run(ekf.ekf_status_once()),
    "ekf-monitor": lambda args: asyncio.run(ekf.monitor_ekf(_parse_duration_arg(args))),
    "rc-status": lambda args: asyncio.run(rc_channels.rc_channels_once()),
    "rc-monitor": lambda args: asyncio.run(rc_channels.monitor_rc_channels(_parse_duration_arg(args))),
    "heartbeat-monitor": lambda args: heartbeat.monitor_heartbeat(
        args[1], _parse_duration_arg(args, start_idx=2)
    ),

    # Configuration commands (sync)
    "compare-params": lambda args: config.compare_params_with_defaults(*_parse_serial_args(args)),
    "configure-telem2": lambda args: config.configure_telem2(*_parse_serial_args(args)),
    "reset-params": lambda args: config.reset_params(*_parse_serial_args(args)),
    "reboot": lambda args: config.reboot(*_parse_serial_args(args)),
}


def main(argv: list[str] = None) -> None:
    """Main entry point.

    Args:
        argv: Command line arguments (defaults to sys.argv[1:])
    """
    args = argv if argv is not None else sys.argv[1:]

    # Default command if none specified
    if not args:
        asyncio.run(flight.takeoff())
        return

    cmd = args[0]

    # Look up and execute command handler
    handler = COMMAND_HANDLERS.get(cmd)
    if handler:
        handler(args)
    else:
        print(f"Unknown command: {cmd}")
        print(f"Available commands: {', '.join(sorted(COMMAND_HANDLERS.keys()))}")
        sys.exit(1)


if __name__ == "__main__":
    main()
