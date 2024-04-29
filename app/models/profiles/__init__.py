from pathlib import Path

from lxml import etree

from app.models.profiles.exceptions import ProfileVersionRetiredError
from app.models.profiles.profile import Profile
from app.models.profiles.profile_1_1 import (
    BasicProfile11,
    MaterialArtworkProfile11,
    NewspaperProfile11,
)

NAMESPACES = {
    "mets": "http://www.loc.gov/METS/",
    "csip": "https://DILCIS.eu/XML/METS/CSIPExtensionMETS",
}


def determine_profile(path: Path) -> Profile:
    """Parse the root METS in order to determine the profile.

    Returns:
        The instantiated Profile
    Raises:
        ValueError:
            - If the package METS could not be parsed.
            - If there is no profile information in the package METS.
            - If the profile is not known.
        ProfileVersionRetiredError: When the profile of the incoming SIP is retired.
    """
    try:
        root = etree.parse(path.joinpath("data", "mets.xml"))
    except (etree.ParseError, OSError) as e:
        raise ValueError(f"METS could not be parsed: {e}.")

    # Parse the meemoo profile in the IE METS
    try:
        profile_type = root.xpath(
            "/mets:mets/@csip:OTHERCONTENTINFORMATIONTYPE",
            namespaces=NAMESPACES,
        )[0]
    except IndexError:
        raise ValueError(
            "METS does not contain a OTHERCONTENTINFORMATIONTYPE attribute."
        )

    if profile_type == "https://data.hetarchief.be/id/sip/1.0/basic":
        raise ProfileVersionRetiredError("The basic profile version 1.0 is retired!")
    elif profile_type == BasicProfile11.profile_name():
        return BasicProfile11(path)
    elif profile_type == MaterialArtworkProfile11.profile_name():
        return MaterialArtworkProfile11(path)
    elif profile_type == NewspaperProfile11.profile_name():
        return NewspaperProfile11(path)

    raise ValueError(f"Profile not known: {profile_type}.")
