"""EKF and sensor telemetry queries"""
import asyncio
from src.mavsdk.connection import connect


async def monitor_ekf(duration: float = 10.0) -> None:
    """Monitor EKF status and position for specified duration."""
    d = await connect()
    start_time = asyncio.get_event_loop().time()

    print("-- Monitoring EKF --\n")

    async for health in d.telemetry.health():
        if (asyncio.get_event_loop().time() - start_time) >= duration:
            break
        print(f"Global: {'OK' if health.is_global_position_ok else 'FAIL'} | "
              f"Local: {'OK' if health.is_local_position_ok else 'FAIL'}")
        await asyncio.sleep(1.0)


async def ekf_status_once() -> None:
    """Get single snapshot of EKF status."""
    d = await connect()

    async for health in d.telemetry.health():
        print(f"Global position: {health.is_global_position_ok}")
        print(f"Local position:  {health.is_local_position_ok}")
        break

    async for position in d.telemetry.position():
        print(f"Lat: {position.latitude_deg:.7f}° Lon: {position.longitude_deg:.7f}°")
        print(f"Alt: {position.absolute_altitude_m:.2f}m")
        break
