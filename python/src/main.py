"""CLI entry point"""
import asyncio
import sys
from src.mavsdk.commands import flight, shell, offboard
from src.mavsdk.telemetry import ekf
from src.mavlink.telemetry import rc_channels
from src.config import pixhawk


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

    # Configuration & Diagnostics
    elif args[0] == "test-connection":
        if len(args) < 2:
            print("Usage: test-connection <port> [baud]")
            sys.exit(1)
        port = args[1]
        baud = int(args[2]) if len(args) > 2 else 57600
        success = pixhawk.test_connection(port, baud)
        sys.exit(0 if success else 1)
    elif args[0] == "scan-ports":
        pixhawk.scan_ports()

    else:
        print(f"Unknown command: {args[0]}")
        sys.exit(1)


if __name__ == "__main__":
    main()
