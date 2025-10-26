"""MAVLink parameter encoding/decoding utilities

MAVLink transmits all parameter values as floats (4 bytes) over the wire.
For integer parameter types, the bytes must be reinterpreted rather than simply cast.
"""
import struct
from pymavlink import mavutil


def encode_param_value(value: int, param_type: int) -> float:
    """Convert integer value to float for MAVLink parameter transmission.

    For integer parameter types, pack the integer as bytes and unpack as float.

    Args:
        value: Integer value to encode
        param_type: MAVLink parameter type (MAV_PARAM_TYPE_*)

    Returns:
        float: Encoded value suitable for MAVLink transmission
    """
    type_map = {
        mavutil.mavlink.MAV_PARAM_TYPE_UINT8: ('B', 'f'),
        mavutil.mavlink.MAV_PARAM_TYPE_INT8: ('b', 'f'),
        mavutil.mavlink.MAV_PARAM_TYPE_UINT16: ('H', 'f'),
        mavutil.mavlink.MAV_PARAM_TYPE_INT16: ('h', 'f'),
        mavutil.mavlink.MAV_PARAM_TYPE_UINT32: ('I', 'f'),
        mavutil.mavlink.MAV_PARAM_TYPE_INT32: ('i', 'f'),
    }

    if param_type in type_map:
        int_fmt, float_fmt = type_map[param_type]
        # Pack as integer bytes, pad to 4 bytes, unpack as float
        int_bytes = struct.pack(int_fmt, value)
        padded_bytes = int_bytes + b'\x00' * (4 - len(int_bytes))
        return struct.unpack(float_fmt, padded_bytes)[0]
    else:
        # For REAL32, just return as float
        return float(value)


def decode_param_value(param_value: float, param_type: int) -> int:
    """Convert float from MAVLink parameter to actual integer value.

    For integer parameter types, pack the float as bytes and unpack as integer.

    Args:
        param_value: Float value received from MAVLink
        param_type: MAVLink parameter type (MAV_PARAM_TYPE_*)

    Returns:
        int: Decoded integer value
    """
    type_map = {
        mavutil.mavlink.MAV_PARAM_TYPE_UINT8: ('f', 'B'),
        mavutil.mavlink.MAV_PARAM_TYPE_INT8: ('f', 'b'),
        mavutil.mavlink.MAV_PARAM_TYPE_UINT16: ('f', 'H'),
        mavutil.mavlink.MAV_PARAM_TYPE_INT16: ('f', 'h'),
        mavutil.mavlink.MAV_PARAM_TYPE_UINT32: ('f', 'I'),
        mavutil.mavlink.MAV_PARAM_TYPE_INT32: ('f', 'i'),
    }

    if param_type in type_map:
        float_fmt, int_fmt = type_map[param_type]
        # Pack as float bytes, extract needed bytes, unpack as integer
        float_bytes = struct.pack(float_fmt, param_value)
        int_size = struct.calcsize(int_fmt)
        return struct.unpack(int_fmt, float_bytes[:int_size])[0]
    else:
        # For REAL32, just return as int
        return int(param_value)
