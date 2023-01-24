from pathlib import Path
import json

from viaa.configuration import ConfigParser
from viaa.observability import logging
from cloudevents.events import Event, EventOutcome, EventAttributes, PulsarBinding

from app.models.profile import (
    BasicProfile,
    GraphNotConformError,
    GraphParseError,
    Profile,
)
from app.services.pulsar import (
    PulsarClient,
    SIP_VALIDATE_XSD_TOPIC,
    SIP_LOAD_GRAPH_TOPIC,
    SIP_VALIDATE_SHACL_TOPIC,
)
from lxml import etree

APP_NAME = "sipin-sip-validator"


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

    def produce_event(
        self,
        topic: str,
        data: dict,
        subject: str,
        outcome: EventOutcome,
        correlation_id: str,
    ):
        """Produce an event on a Pulsar topic.

        Args:
            topic: The topic to send the cloudevent to.
            data: The data payload.
            subject: The subject of the event.
            outcome: The attributes outcome of the Event.
            correlation_id: The correlation ID.
        """
        attributes = EventAttributes(
            type=topic,
            source=APP_NAME,
            subject=subject,
            correlation_id=correlation_id,
            outcome=outcome,
        )

        event = Event(attributes, data)
        self.pulsar_client.produce_event(topic, event)

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

                    # Validate XML files
                    xml_validation_errors = profile.validate_metadata()
                    if xml_validation_errors:
                        self.produce_event(
                            SIP_VALIDATE_XSD_TOPIC,
                            {
                                "message": "Metadata files are not valid against XSD",
                                "errors": [str(e) for e in xml_validation_errors],
                            },
                            msg_data["destination"],
                            EventOutcome.FAIL,
                            incoming_event.correlation_id,
                        )
                        self.pulsar_client.acknowledge(msg)
                        return

                    self.produce_event(
                        SIP_VALIDATE_XSD_TOPIC,
                        {
                            "message": "Metadata files are valid against XSD",
                        },
                        msg_data["destination"],
                        EventOutcome.SUCCESS,
                        incoming_event.correlation_id,
                    )

                    # Parse graph
                    try:
                        graph = profile.parse_graph()
                    except GraphParseError as e:
                        self.produce_event(
                            SIP_LOAD_GRAPH_TOPIC,
                            {
                                "message": "Cannot transform metadata into a graph.",
                                "errors": str(e),
                            },
                            msg_data["destination"],
                            EventOutcome.FAIL,
                            incoming_event.correlation_id,
                        )
                        self.pulsar_client.acknowledge(msg)
                        return

                    self.produce_event(
                        SIP_LOAD_GRAPH_TOPIC,
                        {
                            "message": "Metadata can be transformed into a graph.",
                        },
                        msg_data["destination"],
                        EventOutcome.SUCCESS,
                        incoming_event.correlation_id,
                    )

                    # Validate graph
                    try:
                        profile.validate_graph(graph)
                    except GraphNotConformError as e:
                        self.produce_event(
                            SIP_VALIDATE_SHACL_TOPIC,
                            {
                                "message": "Graph is not conform.",
                                "errors": str(e),
                            },
                            msg_data["destination"],
                            EventOutcome.FAIL,
                            incoming_event.correlation_id,
                        )
                        self.pulsar_client.acknowledge(msg)
                        return

                    # Send event
                    self.produce_event(
                        SIP_VALIDATE_SHACL_TOPIC,
                        {
                            "message": "Graph is conform.",
                            "metadata_graph": json.loads(
                                graph.serialize(format="json-ld")
                            ),
                        },
                        msg_data["destination"],
                        EventOutcome.SUCCESS,
                        incoming_event.correlation_id,
                    )

                    self.pulsar_client.acknowledge(msg)

            except Exception as e:
                # Generic catch all remaining errors.
                self.log.error(f"Error: {e}")
                # Message failed to be processed
                self.pulsar_client.acknowledge(msg)
        self.pulsar_client.close()
