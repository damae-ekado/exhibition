from astropy.coordinates import SkyCoord, AltAz, EarthLocation
from astropy.time import Time
import astropy.units as u


def convert_to_altaz(
    ra: float,
    dec: float,
    observation_time: str,
    latitude: float,
    longitude: float
):
    sky_coord = SkyCoord(ra=ra * u.deg, dec=dec * u.deg)

    location = EarthLocation(lat=latitude * u.deg, lon=longitude * u.deg)

    altaz = sky_coord.transform_to(
        AltAz(
            obstime=Time(observation_time),
            location=location
        )
    )

    return altaz.az.deg, altaz.alt.deg
