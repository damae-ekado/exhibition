from services.analysis_service import analyze_two_points


def main():

    file_path = "example.fits"

    latitude = 37.5665
    longitude = 126.9780

    point1 = (1200, 850)
    point2 = (1300, 900)

    result = analyze_two_points(
        file_path,
        point1,
        point2,
        latitude,
        longitude
    )

    print(result)


if __name__ == "__main__":
    main()
