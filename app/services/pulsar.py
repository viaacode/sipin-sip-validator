#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pulsar import Client, Consumer

from viaa.configuration import ConfigParser
from viaa.observability import logging
from cloudevents.events import Event, CEMessageMode, PulsarBinding


SIP_VALIDATE_XSD_TOPIC = "sip.validate.xsd"
SIP_LOAD_GRAPH_TOPIC = "sip.loadgraph"
SIP_VALIDATE_SHACL_TOPIC = "sip.validate.shacl"


class PulsarClient:
    """Abstraction for a Pulsar Client.

    Attributes:
        log: The logger.
        pulsar_config: The config regarding Pulsar.
        app_config: The config regarding the service.
        client: The actual Pulsar client.
        consumer: A Pulsar consumer to read messages from.
        producer: A Pulsar producer to send messages to.
    """

    def __init__(self):
        config_parser = ConfigParser()
        self.log = logging.get_logger(__name__, config=config_parser)
        self.pulsar_config: dict = config_parser.app_cfg["pulsar"]
        self.app_config: dict = config_parser.app_cfg["sip-parser"]
        self.client: Client = Client(
            f'pulsar://{self.pulsar_config["host"]}:{self.pulsar_config["port"]}'
        )
        self.consumer: Consumer = self.client.subscribe(
            self.app_config["consumer_topic"], "sipin-sip-parser"
        )
        self.log.info(f"Started consuming topic: {self.app_config['consumer_topic']}")
        self.producers = {}

    def produce_event(self, topic: str, event: Event):
        """Produce a cloudevent on a topic.

        If there is no producer yet for the given topic, a new one will be created.

        Args:
            topic: The topic to send the cloudevent to.
            event: The cloudevent to send to the topic.
        """
        if topic not in self.producers:
            self.producers[topic] = self.client.create_producer(topic)

        msg = PulsarBinding.to_protocol(event, CEMessageMode.STRUCTURED)
        self.producers[topic].send(
            msg.data,
            properties=msg.attributes,
            event_timestamp=event.get_event_time_as_int(),
        )

    def receive(self):
        """Receive a message from the open consumer.

        Returns:
            The message.
        """
        return self.consumer.receive()

    def acknowledge(self, msg):
        """Acknowledge a message on the open consumer.

        Args:
            msg: The message to acknowledge.
        """
        self.consumer.acknowledge(msg)

    def negative_acknowledge(self, msg):
        """Nack a message on the open consumer.

        Args:
            msg: The message to nack.
        """
        self.consumer.negative_acknowledge(msg)

    def close(self):
        """Close the open producers and consumer."""
        for producer in self.producers.values():
            producer.close()
        self.consumer.close()
