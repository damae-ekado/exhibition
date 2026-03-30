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
