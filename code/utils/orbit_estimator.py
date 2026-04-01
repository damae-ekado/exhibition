import numpy as np


def estimate_inclination(ra1, dec1, ra2, dec2):
    """
    궤도 경사각 근사 계산 (deg)
    """

    # rad 변환
    ra1, dec1, ra2, dec2 = map(
        np.radians,
        [ra1, dec1, ra2, dec2]
    )

    delta_ra = ra2 - ra1
    delta_dec = dec2 - dec1

    # 평균 Dec (cos 보정용)
    mean_dec = (dec1 + dec2) / 2

    # 기울기 계산
    slope = delta_dec / (delta_ra * np.cos(mean_dec))

    inclination = np.arctan(slope)

    return abs(np.degrees(inclination))