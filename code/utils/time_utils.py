from astropy.time import Time


def get_observation_time(header):
    """
    FITS header에서 관측 시간 반환
    """
    if "DATE-OBS" not in header:
        raise ValueError("DATE-OBS not found in header")

    return Time(header["DATE-OBS"], format='isot', scale='utc')

def calculate_time_difference(header1, header2):
    """
    두 FITS header 간 시간 차 (초)
    """
    t1 = get_observation_time(header1)
    t2 = get_observation_time(header2)

    return abs((t2 - t1).sec)