"""CLI entry point"""
import asyncio
import sys
from src.mavsdk.commands import flight, shell, offboard
from src.mavsdk.telemetry import ekf
from src.mavlink.telemetry import rc_channels


def main(argv: list[str] = None) -> None:
    """Main entry point."""
    args = argv if argv is not None else sys.argv[1:]

    if not args:
        asyncio.run(flight.takeoff())

    # Commands
    elif args[0] == "takeoff":
        asyncio.run(flight.takeoff())
    elif args[0] == "shell" and len(args) > 1:
        asyncio.run(shell.execute(' '.join(args[1:])))
    elif args[0] == "offboard":
        # Parse offboard control parameters
        if len(args) < 5:
            print("Usage: offboard <forward> <lateral> <vertical> <yaw_rate> [duration]")
            sys.exit(1)
        forward = float(args[1])
        lateral = float(args[2])
        vertical = float(args[3])
        yaw_rate = float(args[4])
        duration = float(args[5]) if len(args) > 5 else 10.0
        asyncio.run(offboard.offboard_control(forward, lateral, vertical, yaw_rate, duration))
    elif args[0] == "offboard-hover":
        asyncio.run(offboard.test_hover())

    # Telemetry
    elif args[0] == "ekf-status":
        asyncio.run(ekf.ekf_status_once())
    elif args[0] == "ekf-monitor":
        duration = float(args[1]) if len(args) > 1 else 10.0
        asyncio.run(ekf.monitor_ekf(duration))
    elif args[0] == "rc-status":
        asyncio.run(rc_channels.rc_channels_once())
    elif args[0] == "rc-monitor":
        duration = float(args[1]) if len(args) > 1 else 10.0
        asyncio.run(rc_channels.monitor_rc_channels(duration))

    else:
        print(f"Unknown command: {args[0]}")
        sys.exit(1)


if __name__ == "__main__":
    main()
