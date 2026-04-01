from astropy.wcs import WCS
import numpy as np


def create_approx_wcs(pixel_points, sky_points):
    """
    최소 3개 기준별로 근사 WCS 생성
    """

    wcs = WCS(naxis=2)

    ref_pixel = pixel_points[0]
    ref_sky = sky_points[0]

    wcs.wcs.crpix = [ref_pixel[0], ref_pixel[1]]
    wcs.wcs.crval = [ref_sky[0], ref_sky[1]]

    # 단순 선형 근사 (초기값)
    wcs.wcs.cd = np.array([
        [1e-5, 0],
        [0, 1e-5]
    ])

    wcs.wcs.ctype = ["RA---TAN", "DEC--TAN"]

    return wcs