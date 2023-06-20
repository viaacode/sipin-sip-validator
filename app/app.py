from pathlib import Path

from viaa.configuration import ConfigParser
from viaa.observability import logging
from cloudevents.events import Event, EventOutcome, EventAttributes, PulsarBinding
from pulsar import Message

from app.models.bag import (
    Bag,
    BagParseError,
    BagNotValidError,
)
from app.models.profile import (
    determine_profile,
    GraphNotConformError,
    GraphParseError,
)
from app.services.pulsar import (
    PulsarClient,
)

APP_NAME = "sipin-sip-validator"
METADATA_GRAPH_FMT = "turtle"


class EventListener:
    def __init__(self):
        config_parser = ConfigParser()
        self.log = logging.get_logger(__name__, config=config_parser)
        self.config = config_parser.app_cfg
        # Init Pulsar client
        self.pulsar_client = PulsarClient()

        # Topics
        app_config = self.config["sip-parser"]
        self.bag_validate_topic = app_config["bag_validate_topic"]
        self.sip_validate_xsd_topic = app_config["sip_validate_xsd_topic"]
        self.sip_load_graph_topic = app_config["sip_load_graph_topic"]
        self.sip_validate_shacl_topic = app_config["sip_validate_shacl_topic"]

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

    def handle_incoming_message(self, message: Message):
        try:
            incoming_event = PulsarBinding.from_protocol(message)
            self.log.debug(f"Incoming event: {incoming_event.get_data()}")
            if (
                incoming_event.has_successful_outcome()
                and incoming_event.get_data().get("outcome") != EventOutcome.FAIL
            ):
                # Get data of event
                msg_data = incoming_event.get_data()
                bag_path = Path(msg_data["destination"])

                bag = Bag(bag_path)
                # Parse and validate bag
                try:
                    bag.parse_validate()
                except (BagParseError) as e:
                    self.log.error(f"'{bag_path}' could not be parsed: {str(e)}")
                    self.produce_event(
                        self.bag_validate_topic,
                        {
                            "message": f"'{bag_path}' could not be parsed: {str(e)}",
                        },
                        msg_data["destination"],
                        EventOutcome.FAIL,
                        incoming_event.correlation_id,
                    )
                    self.pulsar_client.acknowledge(message)
                    return
                except (BagNotValidError) as e:
                    self.log.error(f"'{bag_path}' is not a valid bag: {str(e)}")
                    self.produce_event(
                        self.bag_validate_topic,
                        {
                            "message": f"'{bag_path}' is not a valid bag: {str(e)}",
                        },
                        msg_data["destination"],
                        EventOutcome.FAIL,
                        incoming_event.correlation_id,
                    )
                    self.pulsar_client.acknowledge(message)
                    return

                self.produce_event(
                    self.bag_validate_topic,
                    {"message": f"{bag_path} is a valid bag"},
                    msg_data["destination"],
                    EventOutcome.SUCCESS,
                    incoming_event.correlation_id,
                )

                # Determine profile
                profile = determine_profile(bag_path)

                # Validate XML files
                xml_validation_errors = profile.validate_metadata()
                if xml_validation_errors:
                    self.log.error(
                        f"{bag_path}: Metadata files are not valid against XSD",
                        errors=[str(e) for e in xml_validation_errors],
                    )
                    self.produce_event(
                        self.sip_validate_xsd_topic,
                        {
                            "message": "Metadata files are not valid against XSD",
                            "errors": [str(e) for e in xml_validation_errors],
                        },
                        msg_data["destination"],
                        EventOutcome.FAIL,
                        incoming_event.correlation_id,
                    )
                    self.pulsar_client.acknowledge(message)
                    return

                self.produce_event(
                    self.sip_validate_xsd_topic,
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
                    self.log.error(
                        f"{bag_path}: Cannot transform metadata into a graph.",
                        errors=str(e),
                    )
                    self.produce_event(
                        self.sip_load_graph_topic,
                        {
                            "message": "Cannot transform metadata into a graph.",
                            "errors": str(e),
                        },
                        msg_data["destination"],
                        EventOutcome.FAIL,
                        incoming_event.correlation_id,
                    )
                    self.pulsar_client.acknowledge(message)
                    return

                self.produce_event(
                    self.sip_load_graph_topic,
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
                    self.log.error(f"{bag_path}: Graph is not conform.", errors=str(e))
                    self.produce_event(
                        self.sip_validate_shacl_topic,
                        {
                            "message": "Graph is not conform.",
                            "errors": str(e),
                        },
                        msg_data["destination"],
                        EventOutcome.FAIL,
                        incoming_event.correlation_id,
                    )
                    self.pulsar_client.acknowledge(message)
                    return

                # Send event
                self.produce_event(
                    self.sip_validate_shacl_topic,
                    {
                        "message": "Graph is conform.",
                        "metadata_graph_fmt": METADATA_GRAPH_FMT,
                        "metadata_graph": graph.serialize(format=METADATA_GRAPH_FMT),
                    },
                    msg_data["destination"],
                    EventOutcome.SUCCESS,
                    incoming_event.correlation_id,
                )

                self.pulsar_client.acknowledge(message)

                self.log.info(f"'{bag_path}' is a valid and conform SIP.")

        except Exception as e:
            # Generic catch all remaining errors.
            self.log.error(f"Error: {e}")
            # Message failed to be processed
            self.pulsar_client.negative_acknowledge(message)

    def main(self):
        while True:
            msg = self.pulsar_client.receive()
            self.handle_incoming_message(msg)

        self.pulsar_client.close()
