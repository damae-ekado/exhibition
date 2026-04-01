import numpy as np
from scipy.ndimage import shift

ARCSEC_PER_SEC = 15.041  # IAU 기준


def calculate_star_shift(
    latitude_rad: float,
    hour_angle_rad: float,
    declination_rad: float,
    exposure_sec: float,
    plate_scale_arcsec_per_pixel: float
):
    """
    별 궤적 기반 픽셀 이동량 계산
    """

    theta = np.arctan2(
        np.cos(latitude_rad) * np.sin(hour_angle_rad),
        np.sin(latitude_rad) * np.cos(declination_rad)
        - np.cos(latitude_rad) * np.sin(declination_rad) * np.cos(hour_angle_rad)
    )

    shift_pixels = (
        ARCSEC_PER_SEC * exposure_sec
    ) / plate_scale_arcsec_per_pixel

    delta_x = shift_pixels * np.cos(theta)

    # 이미지 좌표계 보정 (y축 반전)
    delta_y = -shift_pixels * np.sin(theta)

    return delta_x, delta_y


def apply_inverse_shift(image_data, delta_x, delta_y):
    """
    이미지 역방향 shift
    """

    return shift(
        image_data,
        shift=(-delta_y, -delta_x),
        order=1  # bilinear interpolation
    )