from dataclasses import dataclass


@dataclass
class SatellitePoint:
    x: float
    y: float

    ra: float = 0.0
    dec: float = 0.0

    az: float = 0.0
    alt: float = 0.0
