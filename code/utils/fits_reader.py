from astropy.io import fits
from astropy.wcs import WCS


def load_fits_file(file_path: str):
    """
    FITS 파일을 읽어 이미지 데이터와 헤더를 반환한다.
    """

    with fits.open(file_path) as hdul:
        image_data = hdul[0].data
        header = hdul[0].header

    return image_data, header


def get_wcs(header):
    """
    FITS 헤더에서 WCS 객체 생성
    """

    wcs = WCS(header)
    return wcs


def pixel_to_skycoord(
    x: float,
    y: float,
    wcs: WCS
):
    """
    픽셀 좌표를 천구 좌표(RA, DEC)로 변환
    """

    sky_coord = wcs.pixel_to_world(x, y)

    ra = sky_coord.ra.deg
    dec = sky_coord.dec.deg

    return ra, dec