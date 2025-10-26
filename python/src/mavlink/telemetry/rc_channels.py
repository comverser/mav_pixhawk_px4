"""RC channel telemetry via MAVLink"""
import time
from src.mavlink.connection import connect


def monitor_rc_channels(duration: float = 10.0) -> None:
    """Monitor RC channel values for specified duration."""
    mav = connect()

    print("\n-- Monitoring RC Channels --")
    print("Ch1-4 typically: Roll, Pitch, Throttle, Yaw")
    print("Values range: 1000-2000 (1500 = center)\n")

    start_time = time.time()

    while (time.time() - start_time) < duration:
        # Blocking receive with timeout
        msg = mav.recv_match(type='RC_CHANNELS', blocking=True, timeout=1.0)

        if msg:
            # RC_CHANNELS provides up to 18 channels
            channels = [
                msg.chan1_raw, msg.chan2_raw, msg.chan3_raw, msg.chan4_raw,
                msg.chan5_raw, msg.chan6_raw, msg.chan7_raw, msg.chan8_raw
            ]

            # Display first 8 channels
            print(f"CH1: {channels[0]:4d} | CH2: {channels[1]:4d} | "
                  f"CH3: {channels[2]:4d} | CH4: {channels[3]:4d} | "
                  f"CH5: {channels[4]:4d} | CH6: {channels[5]:4d} | "
                  f"CH7: {channels[6]:4d} | CH8: {channels[7]:4d}")

        time.sleep(0.1)  # Small delay between readings

    print("\nMonitoring complete")


def rc_channels_once() -> None:
    """Get single snapshot of RC channel values."""
    mav = connect()

    # Wait for RC_CHANNELS message
    msg = mav.recv_match(type='RC_CHANNELS', blocking=True, timeout=5.0)

    if msg:
        print("RC Channel Values:")
        print(f"  Channel 1 (Roll):     {msg.chan1_raw}")
        print(f"  Channel 2 (Pitch):    {msg.chan2_raw}")
        print(f"  Channel 3 (Throttle): {msg.chan3_raw}")
        print(f"  Channel 4 (Yaw):      {msg.chan4_raw}")
        print(f"  Channel 5:            {msg.chan5_raw}")
        print(f"  Channel 6:            {msg.chan6_raw}")
        print(f"  Channel 7:            {msg.chan7_raw}")
        print(f"  Channel 8:            {msg.chan8_raw}")
        print(f"\n  RSSI: {msg.rssi} dB")
    else:
        print("No RC_CHANNELS message received (timeout)")
