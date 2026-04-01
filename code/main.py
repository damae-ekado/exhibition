from utils.fits_reader import (
    load_fits_file,
    get_wcs,
    pixel_to_skycoord,
    has_valid_wcs
)

from utils.astrometry_api import solve_astrometry
from utils.angle_calculator import calculate_angular_distance
from utils.region_reader import load_region
from utils.time_utils import calculate_time_difference
from utils.orbit_estimator import estimate_inclination


def process_wcs(file_path, solved_path):
    """
    WCS 없으면 astrometry 수행 후 WCS 반환
    """
    image_data, header = load_fits_file(file_path)

    if has_valid_wcs(header):
        print(f"{file_path}: WCS already exists.")
        return header, get_wcs(header)

    print(f"{file_path}: No WCS found. Running astrometry...")

    solved_file = solve_astrometry(file_path, solved_path)

    if solved_file is None:
        raise RuntimeError("Astrometry failed.")

    image_data, header = load_fits_file(solved_file)
    print(f"{file_path}: Astrometry solved.")

    return header, get_wcs(header)


def main():

    file_path_1 = "example.fit"
    file_path_2 = "example2.fit"
    region_path = "example"

    # 1. WCS 처리 (각각 따로)
    header1, wcs1 = process_wcs(file_path_1, "solved1.fits")
    header2, wcs2 = process_wcs(file_path_2, "solved2.fits")

    # 2. 시간 차 계산
    delta_t = calculate_time_difference(header1, header2)
    print("Time difference (s):", delta_t)

    # 3. region 좌표 읽기
    (x1, y1), (x2, y2) = load_region(region_path)

    print("Pixel Start:", x1, y1)
    print("Pixel End:", x2, y2)

    # 4. 각 이미지에서 좌표 변환
    ra1, dec1 = pixel_to_skycoord(x1, y1, wcs1)
    ra2, dec2 = pixel_to_skycoord(x2, y2, wcs2)

    print("Start (RA, Dec):", ra1, dec1)
    print("End (RA, Dec):", ra2, dec2)

    # 5. 각거리 계산
    angle = calculate_angular_distance(ra1, dec1, ra2, dec2)
    print("Angular Distance (deg):", angle)

    # 6. 각속도 계산
    omega = angle / delta_t
    print("Angular Velocity (deg/s):", omega)

    # 7. 궤도 경사각 계산
    inclination = estimate_inclination(ra1, dec1, ra2, dec2)
    print("Estimated Inclination (deg):", inclination)


if __name__ == "__main__":
    main()