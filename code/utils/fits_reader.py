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
    FITS 헤더에서 WCS 객체 생성 (검증 포함)
    """
    wcs = WCS(header)

    if not wcs.has_celestial:
        raise ValueError("Invalid WCS: no celestial component")

    return wcs


def pixel_to_skycoord(
    x: float,
    y: float,
    wcs: WCS
):
    """
    픽셀 좌표를 천구 좌표(RA, DEC)로 변환
    """

    ra, dec = wcs.wcs_pix2world(x, y, 0)
    
    return ra, dec

def has_valid_wcs(header) -> bool:
    return (
        "CTYPE1" in header and
        "CTYPE2" in header and
        "CRVAL1" in header and
        "CRVAL2" in header and
        (
            "CD1_1" in header or "CDELT1" in header
        )
    )