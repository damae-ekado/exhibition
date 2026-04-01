import math


def calculate_angular_distance(
    az1: float,
    alt1: float,
    az2: float,
    alt2: float
) -> float:

    az1, alt1, az2, alt2 = map(
        math.radians,
        [az1, alt1, az2, alt2]
    )

    cos_theta = (
        math.sin(alt1) * math.sin(alt2)
        + math.cos(alt1) * math.cos(alt2) * math.cos(az1 - az2)
    )

    return math.degrees(math.acos(cos_theta))


def calculate_angular_velocity(
    delta_theta: float,
    delta_time: float
) -> float:

    if delta_time <= 0:
        raise ValueError("delta_time must be positive")

    return delta_theta / delta_time

from config.constants import EARTH_ROTATION_RATE


def correct_angular_velocity(observed_velocity: float) -> float:
    """
    지구 자전에 의한 각속도 성분을 제거한다.
    """

    return observed_velocity - EARTH_ROTATION_RATE
