"""CLI entry point"""
import asyncio
import sys
from src.mavsdk.commands import flight, shell, offboard
from src.mavsdk.telemetry import ekf
from src.mavlink.telemetry import rc_channels
from src.mavlink import heartbeat
from src import pixhawk, diagnostics, param_dump, baud_scan, configure_mav0_telem2, uart_loopback_test


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

    # Heartbeat & Connection Testing
    elif args[0] == "test-connection":
        if len(args) < 2:
            print("Usage: test-connection <port> [baud]")
            sys.exit(1)
        port = args[1]
        baud = int(args[2]) if len(args) > 2 else 57600
        success = heartbeat.test_connection(port, baud)
        sys.exit(0 if success else 1)
    elif args[0] == "scan-ports":
        heartbeat.scan_ports()
    elif args[0] == "heartbeat-monitor":
        if len(args) < 2:
            print("Usage: heartbeat-monitor <connection_string> [duration]")
            sys.exit(1)
        connection_string = args[1]
        duration = float(args[2]) if len(args) > 2 else 10.0
        heartbeat.monitor_heartbeat(connection_string, duration)

    # Pixhawk Configuration
    elif args[0] == "check-telem2":
        port = args[1] if len(args) > 1 else "/dev/ttyACM0"
        baud = int(args[2]) if len(args) > 2 else 57600
        pixhawk.check_telem2_config(port, baud)
    elif args[0] == "configure-telem2":
        port = args[1] if len(args) > 1 else "/dev/ttyACM0"
        usb_baud = int(args[2]) if len(args) > 2 else 57600
        telem_baud = int(args[3]) if len(args) > 3 else 921600
        configure_mav0_telem2.configure_mav0_telem2(port, usb_baud, telem_baud)
    elif args[0] == "reboot":
        port = args[1] if len(args) > 1 else "/dev/ttyACM0"
        baud = int(args[2]) if len(args) > 2 else 57600
        pixhawk.reboot_pixhawk(port, baud)

    # Diagnostics
    elif args[0] == "serial-monitor":
        port = args[1] if len(args) > 1 else "/dev/ttyAMA10"
        baud = int(args[2]) if len(args) > 2 else 921600
        duration = float(args[3]) if len(args) > 3 else 10.0
        diagnostics.monitor_raw_serial(port, baud, duration)
    elif args[0] == "param-dump":
        port = args[1] if len(args) > 1 else "/dev/ttyACM0"
        baud = int(args[2]) if len(args) > 2 else 57600
        filter_prefix = args[3] if len(args) > 3 else None
        param_dump.dump_all_params(port, baud, filter_prefix)
    elif args[0] == "baud-scan":
        port = args[1] if len(args) > 1 else "/dev/ttyAMA10"
        try:
            duration = float(args[2]) if len(args) > 2 else 3.0
        except (ValueError, IndexError):
            duration = 3.0
        baud_scan.scan_baud_rates(port, duration)
    elif args[0] == "uart-loopback":
        port = args[1] if len(args) > 1 else "/dev/ttyAMA10"
        baud = int(args[2]) if len(args) > 2 else 921600
        skip_prompt = args[3] == "--skip-prompt" if len(args) > 3 else False
        uart_loopback_test.test_uart_loopback(port, baud, skip_prompt)

    else:
        print(f"Unknown command: {args[0]}")
        sys.exit(1)


if __name__ == "__main__":
    main()
