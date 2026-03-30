import math

MU = 3.986004418e14  # Earth gravitational parameter (m^3/s^2)


def calculate_inclination(
    delta_ra: float,
    delta_dec: float,
    mean_dec: float
) -> float:

    delta_ra_rad = math.radians(delta_ra)
    delta_dec_rad = math.radians(delta_dec)
    mean_dec_rad = math.radians(mean_dec)

    inclination = math.atan(
        delta_dec_rad / (delta_ra_rad * math.cos(mean_dec_rad))
    )

    return math.degrees(inclination)


def calculate_orbital_period(radius: float) -> float:
    return 2 * math.pi * math.sqrt(radius**3 / MU)
