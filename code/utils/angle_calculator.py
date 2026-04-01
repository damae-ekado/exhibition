# utils/angle_calculator.py

import numpy as np


def calculate_angular_distance(
    ra1: float,
    dec1: float,
    ra2: float,
    dec2: float
) -> float:
    """
    두 천구 좌표 사이 각거리 계산 (deg)
    """

    ra1, dec1, ra2, dec2 = map(
        np.radians,
        [ra1, dec1, ra2, dec2]
    )

    cos_theta = (
        np.sin(dec1) * np.sin(dec2)
        + np.cos(dec1) * np.cos(dec2) * np.cos(ra1 - ra2)
    )

    # 수치 안정성 보정
    cos_theta = np.clip(cos_theta, -1.0, 1.0)

    theta = np.arccos(cos_theta)

    return np.degrees(theta)