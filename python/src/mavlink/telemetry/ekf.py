"""EKF and sensor telemetry via MAVLink"""
import time
import math
from src.mavlink.connection import connect


def monitor_ekf(duration: float = 10.0) -> None:
    """Monitor EKF status and position for specified duration."""
    mav = connect()

    print("\n-- Monitoring EKF --")
    print("Lat/Lon in degrees, Alt in meters, Velocity in m/s\n")

    start_time = time.time()

    while (time.time() - start_time) < duration:
        # Get GPS position
        gps_msg = mav.recv_match(type='GLOBAL_POSITION_INT', blocking=True, timeout=1.0)

        # Get local position and velocity
        local_msg = mav.recv_match(type='LOCAL_POSITION_NED', blocking=True, timeout=1.0)

        # Get attitude
        att_msg = mav.recv_match(type='ATTITUDE', blocking=True, timeout=1.0)

        if gps_msg and local_msg and att_msg:
            # GLOBAL_POSITION_INT provides lat/lon in degE7, alt in mm
            lat = gps_msg.lat / 1e7
            lon = gps_msg.lon / 1e7
            alt = gps_msg.alt / 1000.0  # mm to meters

            # LOCAL_POSITION_NED provides velocity in m/s
            vn = local_msg.vx
            ve = local_msg.vy
            vd = local_msg.vz

            # ATTITUDE provides Euler angles in radians
            roll = math.degrees(att_msg.roll)
            pitch = math.degrees(att_msg.pitch)
            yaw = math.degrees(att_msg.yaw)

            print(f"Position: Lat {lat:11.7f}° Lon {lon:11.7f}° Alt {alt:7.2f}m")
            print(f"Velocity: N {vn:6.2f} E {ve:6.2f} D {vd:6.2f} m/s")
            print(f"Attitude: Roll {roll:6.1f}° Pitch {pitch:6.1f}° Yaw {yaw:6.1f}°")
            print()
        else:
            print("Waiting for telemetry data...")

        time.sleep(0.5)

    print("Monitoring complete")


def ekf_status_once() -> None:
    """Get single snapshot of EKF status."""
    mav = connect()

    # Check EKF status from SYS_STATUS
    sys_msg = mav.recv_match(type='SYS_STATUS', blocking=True, timeout=3.0)

    if sys_msg:
        # Decode sensor health from sensors_enabled, sensors_health bitfields
        # Bit 3: GPS (3D fix)
        gps_enabled = bool(sys_msg.onboard_control_sensors_enabled & (1 << 3))
        gps_healthy = bool(sys_msg.onboard_control_sensors_health & (1 << 3))

        print(f"GPS enabled: {gps_enabled}")
        print(f"GPS healthy: {gps_healthy}")
    else:
        print("SYS_STATUS: Not available")

    # Get GPS position
    gps_msg = mav.recv_match(type='GLOBAL_POSITION_INT', blocking=True, timeout=3.0)

    if gps_msg:
        lat = gps_msg.lat / 1e7
        lon = gps_msg.lon / 1e7
        alt = gps_msg.alt / 1000.0
        print(f"Position: Lat {lat:.7f}° Lon {lon:.7f}° Alt {alt:.2f}m")
    else:
        print("Position: Not available (GPS may not be locked)")
