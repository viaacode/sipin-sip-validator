from pathlib import Path

from viaa.configuration import ConfigParser
from viaa.observability import logging

from app.models.profile import BasicProfile, Profile
from app.services.pulsar import PulsarClient
from cloudevents.events import EventOutcome, PulsarBinding
from lxml import etree


NAMESPACES = {
    "mets": "http://www.loc.gov/METS/",
    "csip": "https://DILCIS.eu/XML/METS/CSIPExtensionMETS",
}


class EventListener:
    def __init__(self):
        config_parser = ConfigParser()
        self.log = logging.get_logger(__name__, config=config_parser)
        self.config = config_parser.app_cfg
        # Init Pulsar client
        self.pulsar_client = PulsarClient()

    def determine_profile(self, path: Path) -> Profile:
        """Parse the root METS in order to determine the profile.

        Returns:
            The instantiated Profile
        Raises:
            ValueError:
                - If the package METS could not be parsed.
                - If there is no profile information in the package METS.
                - If the profile is not known.
        """
        try:
            root = etree.parse(path.joinpath("data", "mets.xml"))
        except etree.ParseError as e:
            ValueError(f"METS could not be parsed: {e}.")

        # Parse the meemoo profile in the IE METS
        try:
            profile_type = root.xpath(
                "/mets:mets/@csip:CONTENTINFORMATIONTYPE",
                namespaces=NAMESPACES,
            )[0]
        except IndexError:
            ValueError("METS does not contain a CONTENTINFORMATIONTYPE attribute.")

        if profile_type == "https://data.hetarchief.be/id/sip/1.0/basic":
            return BasicProfile(path)
        raise ValueError(f"Profile not known: {profile_type}.")

    def main(self):
        while True:
            msg = self.pulsar_client.receive()
            try:
                incoming_event = PulsarBinding.from_protocol(msg)
                if (
                    incoming_event.has_successful_outcome()
                    and incoming_event.get_data().get("outcome") != EventOutcome.FAIL
                ):
                    # Get data of event
                    msg_data = incoming_event.get_data()
                    bag_path = Path(msg_data["destination"])

                    # Determine profile
                    profile = self.determine_profile(bag_path)
                    profile.handle()

                    self.pulsar_client.acknowledge(msg)

            except Exception as e:
                self.log.error(f"Error: {e}")
                # Message failed to be processed
                self.pulsar_client.negative_acknowledge(msg)
        self.pulsar_client.close()
