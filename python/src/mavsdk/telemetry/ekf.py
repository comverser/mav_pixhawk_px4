"""EKF and sensor telemetry queries"""
import asyncio
from src.mavsdk.connection import connect


async def monitor_ekf(duration: float = 10.0) -> None:
    """Monitor EKF status and position for specified duration."""
    d = await connect()
    start_time = asyncio.get_event_loop().time()

    print("-- Monitoring EKF --\n")

    while (asyncio.get_event_loop().time() - start_time) < duration:
        try:
            # Get telemetry with timeouts
            health = await asyncio.wait_for(_get_health(d), timeout=2.0)
            position = await asyncio.wait_for(_get_position(d), timeout=2.0)
            velocity = await asyncio.wait_for(_get_velocity(d), timeout=2.0)
            attitude = await asyncio.wait_for(_get_attitude(d), timeout=2.0)

            # Display data
            print(f"Status: Global {'OK' if health.is_global_position_ok else 'FAIL'} | "
                  f"Local {'OK' if health.is_local_position_ok else 'FAIL'}")
            print(f"Position: Lat {position.latitude_deg:.7f}° Lon {position.longitude_deg:.7f}° "
                  f"Alt {position.absolute_altitude_m:.2f}m")
            print(f"Velocity: N {velocity.north_m_s:.2f} E {velocity.east_m_s:.2f} D {velocity.down_m_s:.2f} m/s")
            print(f"Attitude: Roll {attitude.roll_deg:.1f}° Pitch {attitude.pitch_deg:.1f}° Yaw {attitude.yaw_deg:.1f}°")
            print()

            await asyncio.sleep(1.0)
        except asyncio.TimeoutError:
            print("Telemetry timeout - data not available")
            await asyncio.sleep(1.0)
        except asyncio.CancelledError:
            break


async def _get_health(d):
    """Get health status."""
    async for health in d.telemetry.health():
        return health


async def _get_position(d):
    """Get position."""
    async for position in d.telemetry.position():
        return position


async def _get_velocity(d):
    """Get velocity in NED frame."""
    async for velocity in d.telemetry.velocity_ned():
        return velocity


async def _get_attitude(d):
    """Get attitude (Euler angles)."""
    async for attitude in d.telemetry.attitude_euler():
        return attitude


async def ekf_status_once() -> None:
    """Get single snapshot of EKF status."""
    d = await connect()

    async for health in d.telemetry.health():
        print(f"Global position: {health.is_global_position_ok}")
        print(f"Local position:  {health.is_local_position_ok}")
        break

    try:
        async def get_position():
            async for position in d.telemetry.position():
                return position

        position = await asyncio.wait_for(get_position(), timeout=3.0)
        print(f"Lat: {position.latitude_deg:.7f}° Lon: {position.longitude_deg:.7f}°")
        print(f"Alt: {position.absolute_altitude_m:.2f}m")
    except asyncio.TimeoutError:
        print("Position: Not available (timeout - GPS may not be locked)")
