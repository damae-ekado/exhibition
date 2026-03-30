from utils.fits_reader import load_fits_file, get_wcs, pixel_to_skycoord
from services.coordinate_service import convert_to_altaz
from services.trajectory_service import (
    calculate_angular_distance,
    calculate_angular_velocity
)
from services.orbit_service import calculate_inclination


def main():

    file_path = "example.fits"

    observation_time = "2026-03-30T21:00:00"
    latitude = 37.5665
    longitude = 126.9780

    exposure_time = 5.0  # seconds

    # 두 점 (사용자가 입력해야 함)
    point1 = (1200, 850)
    point2 = (1300, 900)

    image_data, header = load_fits_file(file_path)
    wcs = get_wcs(header)

    # RA/DEC 변환
    ra1, dec1 = pixel_to_skycoord(point1[0], point1[1], wcs)
    ra2, dec2 = pixel_to_skycoord(point2[0], point2[1], wcs)

    # Alt/Az 변환
    az1, alt1 = convert_to_altaz(ra1, dec1, observation_time, latitude, longitude)
    az2, alt2 = convert_to_altaz(ra2, dec2, observation_time, latitude, longitude)

    # 각거리
    delta_theta = calculate_angular_distance(az1, alt1, az2, alt2)

    # 각속도
    angular_velocity = calculate_angular_velocity(delta_theta, exposure_time)

    # 경사각
    inclination = calculate_inclination(
        ra2 - ra1,
        dec2 - dec1,
        (dec1 + dec2) / 2
    )

    print("Angular Distance:", delta_theta)
    print("Angular Velocity:", angular_velocity)
    print("Inclination:", inclination)


if __name__ == "__main__":
    main()
