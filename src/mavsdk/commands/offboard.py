"""Offboard control for custom vehicles using trajectory_setpoint reinterpretation"""
import asyncio
from mavsdk.offboard import VelocityBodyYawspeed, OffboardError
from src.mavsdk.connection import connect


async def offboard_control(forward: float, lateral: float, vertical: float,
                          yaw_rate: float, duration: float = 10.0) -> None:
    """
    Control custom vehicle via offboard mode.

    Publishes to trajectory_setpoint uORB topic for custom PX4 module to reinterpret.
    """
    d = await connect()

    async for health in d.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            break

    await d.action.arm()
    await d.offboard.set_velocity_body(VelocityBodyYawspeed(0.0, 0.0, 0.0, 0.0))

    try:
        await d.offboard.start()
    except OffboardError as error:
        print(f"Offboard start failed: {error._result.result}")
        await d.action.disarm()
        return

    print(f"-- Offboard: fwd={forward} lat={lateral} vert={vertical} yaw={yaw_rate}")

    start_time = asyncio.get_event_loop().time()
    while (asyncio.get_event_loop().time() - start_time) < duration:
        await d.offboard.set_velocity_body(
            VelocityBodyYawspeed(forward, lateral, vertical, yaw_rate)
        )
        await asyncio.sleep(0.1)

    await d.offboard.stop()
    await d.action.land()

    async for is_armed in d.telemetry.armed():
        if not is_armed:
            break


async def test_hover() -> None:
    """Hover test."""
    await offboard_control(0.0, 0.0, 0.0, 0.0, 10.0)


async def test_forward() -> None:
    """Forward movement test."""
    await offboard_control(2.0, 0.0, 0.0, 0.0, 10.0)
