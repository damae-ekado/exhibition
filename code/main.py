from utils.fits_reader import load_fits_file
from utils.fits_reader import get_wcs
from utils.fits_reader import pixel_to_skycoord


def main():

    file_path = "example.fits"

    image_data, header = load_fits_file(file_path)

    wcs = get_wcs(header)

    x = 1200
    y = 850

    ra, dec = pixel_to_skycoord(x, y, wcs)

    print("Right Ascension:", ra)
    print("Declination:", dec)


if __name__ == "__main__":
    main()