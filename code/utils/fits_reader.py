from astropy.io import fits
from astropy.wcs import WCS
from typing import Tuple


def load_fits_file(file_path: str) -> Tuple:
    with fits.open(file_path) as hdul:
        image_data = hdul[0].data
        header = hdul[0].header

    return image_data, header


def get_wcs(header) -> WCS:
    return WCS(header)


def pixel_to_skycoord(x: float, y: float, wcs: WCS) -> Tuple[float, float]:
    sky_coord = wcs.pixel_to_world(x, y)

    return sky_coord.ra.deg, sky_coord.dec.deg

def extract_time_info(header):
    """
    FITS 헤더에서 관측 시간과 노출 시간을 추출한다.
    """

    exposure_time = header.get("EXPTIME")
    observation_time = header.get("DATE-OBS")

    if exposure_time is None or observation_time is None:
        raise ValueError("FITS header missing EXPTIME or DATE-OBS")

    return observation_time, exposure_time
