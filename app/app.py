from pathlib import Path

from viaa.configuration import ConfigParser
from viaa.observability import logging

from cloudevents.events import EventOutcome, PulsarBinding
from app.services.pulsar import PulsarClient


class EventListener:
    def __init__(self):
        config_parser = ConfigParser()
        self.log = logging.get_logger(__name__, config=config_parser)
        self.config = config_parser.app_cfg
        # Init Pulsar client
        self.pulsar_client = PulsarClient()

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
                    print(bag_path)

                    self.pulsar_client.acknowledge(msg)

            except Exception as e:
                self.log.error(f"Error: {e}")
                # Message failed to be processed
                self.pulsar_client.negative_acknowledge(msg)
        self.pulsar_client.close()
