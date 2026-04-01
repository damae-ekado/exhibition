from utils.fits_reader import (
    load_fits_file,
    get_wcs,
    pixel_to_skycoord,
    extract_time_info
)
from services.coordinate_service import convert_to_altaz
from services.trajectory_service import (
    calculate_angular_distance,
    calculate_angular_velocity,
    correct_angular_velocity
)
from services.orbit_service import calculate_inclination


def analyze_two_points(
    file_path: str,
    point1: tuple,
    point2: tuple,
    latitude: float,
    longitude: float
):

    image_data, header = load_fits_file(file_path)
    wcs = get_wcs(header)

    observation_time, exposure_time = extract_time_info(header)

    # RA/DEC
    ra1, dec1 = pixel_to_skycoord(point1[0], point1[1], wcs)
    ra2, dec2 = pixel_to_skycoord(point2[0], point2[1], wcs)

    # Alt/Az
    az1, alt1 = convert_to_altaz(ra1, dec1, observation_time, latitude, longitude)
    az2, alt2 = convert_to_altaz(ra2, dec2, observation_time, latitude, longitude)

    # 각거리
    delta_theta = calculate_angular_distance(az1, alt1, az2, alt2)

    # 각속도
    angular_velocity = calculate_angular_velocity(delta_theta, exposure_time)

    # 지구 자전 보정
    corrected_velocity = correct_angular_velocity(angular_velocity)

    # 경사각
    inclination = calculate_inclination(
        ra2 - ra1,
        dec2 - dec1,
        (dec1 + dec2) / 2
    )

    return {
        "angular_distance": delta_theta,
        "angular_velocity": angular_velocity,
        "corrected_velocity": corrected_velocity,
        "inclination": inclination
    }
