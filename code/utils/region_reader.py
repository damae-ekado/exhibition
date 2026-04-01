def load_region(file_path: str):
    """
    DS9 region 파일에서 point 좌표 2개 추출
    """

    points = []

    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()

            if line.startswith("point"):
                coords = line.split("(")[1].split(")")[0]
                x, y = map(float, coords.split(","))
                points.append((x, y))

    if len(points) != 2:
        raise ValueError("point는 반드시 2개여야 함")

    return points[0], points[1]