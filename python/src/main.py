"""CLI entry point"""
import asyncio
import sys
from src.mavsdk.commands import flight, shell, offboard
from src.mavsdk.telemetry import ekf
from src.mavlink.telemetry import rc_channels, heartbeat
from src.mavlink import config


def main(argv: list[str] = None) -> None:
    """Main entry point."""
    args = argv if argv is not None else sys.argv[1:]

    if not args:
        asyncio.run(flight.takeoff())
        return

    cmd = args[0]

    # Commands
    if cmd == "takeoff":
        asyncio.run(flight.takeoff())
    elif cmd == "shell":
        asyncio.run(shell.execute(' '.join(args[1:])))
    elif cmd == "offboard-hover":
        asyncio.run(offboard.test_hover())
    elif cmd == "offboard":
        asyncio.run(offboard.offboard_control(
            float(args[1]), float(args[2]), float(args[3]), float(args[4]),
            float(args[5]) if len(args) > 5 else 10.0
        ))

    # Telemetry
    elif cmd == "ekf-status":
        asyncio.run(ekf.ekf_status_once())
    elif cmd == "ekf-monitor":
        asyncio.run(ekf.monitor_ekf(float(args[1]) if len(args) > 1 else 10.0))
    elif cmd == "rc-status":
        asyncio.run(rc_channels.rc_channels_once())
    elif cmd == "rc-monitor":
        asyncio.run(rc_channels.monitor_rc_channels(float(args[1]) if len(args) > 1 else 10.0))
    elif cmd == "heartbeat-monitor":
        heartbeat.monitor_heartbeat(args[1], float(args[2]) if len(args) > 2 else 10.0)

    # Configuration
    elif cmd == "configure-telem2":
        config.configure_telem2(
            args[1] if len(args) > 1 else "/dev/ttyACM0",
            int(args[2]) if len(args) > 2 else 57600
        )
    elif cmd == "reboot":
        config.reboot(
            args[1] if len(args) > 1 else "/dev/ttyACM0",
            int(args[2]) if len(args) > 2 else 57600
        )

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
