from unittest.mock import patch
import logging

import pytest
from cloudevents.events import EventOutcome

from app.app import EventListener
from app.models.profile import GraphParseError, GraphNotConformError
from app.models.bag import BagParseError, BagNotValidError


class PulsarEventMock:
    def __init__(self, attributes: dict, data: dict):
        self.attributes = attributes
        self.data = data
        self.correlation_id = (
            attributes.get("correlation_id")
            if attributes.get("correlation_id")
            else "1"
        )

    def get_data(self) -> dict:
        return self.data

    def properties(self) -> dict:
        return self.attributes

    def has_successful_outcome(self) -> bool:
        return self.attributes.get("outcome") != EventOutcome.FAIL


class TestEventListener:
    @pytest.fixture
    def event(self):
        return PulsarEventMock(
            {
                "content_type": "application/cloudevents+json; charset=utf-8",
                "correlation_id": "555",
                "datacontenttype": "application/json",
                "id": "111",
                "outcome": "success",
                "source": "SIP Validator Test",
                "specversion": "1.0",
                "subject": "test",
                "time": "2023-01-30T12:35:01.668187+00:00",
                "type": "test qas",
            },
            {"destination": "test"},
        )

    @pytest.fixture
    @patch("app.app.PulsarClient")
    def event_listener(self, pulsar_client):
        event_listener = EventListener()
        return event_listener

    @patch("app.app.PulsarBinding")
    @patch("app.app.Bag")
    @patch("app.app.EventListener.produce_event")
    @patch("app.app.determine_profile")
    def test_handle_incoming_message(
        self,
        determine_profile_mock,
        produce_event_mock,
        bag_mock,
        pulsar_binding_mock,
        event_listener,
        event,
        caplog,
    ):
        # Arrange
        # Return an CloudEvent from a Pulsar message
        pulsar_binding_mock.from_protocol.return_value = event
        # There should be no errors when validating the metadata
        determine_profile_mock().validate_metadata.return_value = []
        # Return JSON serialized in byte format when parsing the graph
        determine_profile_mock().parse_graph().serialize.return_value = (
            b'{"graph": "info"}'
        )

        # Act
        event_listener.handle_incoming_message("")

        # Assert
        assert [call.args for call in produce_event_mock.call_args_list] == [
            (
                "bag.validate",
                {"message": "test is a valid bag"},
                "test",
                EventOutcome.SUCCESS,
                "555",
            ),
            (
                "sip.validate.xsd",
                {"message": "Metadata files are valid against XSD"},
                "test",
                EventOutcome.SUCCESS,
                "555",
            ),
            (
                "sip.loadgraph",
                {"message": "Metadata can be transformed into a graph."},
                "test",
                EventOutcome.SUCCESS,
                "555",
            ),
            (
                "sip.validate.shacl",
                {"message": "Graph is conform.", "metadata_graph": {"graph": "info"}},
                "test",
                EventOutcome.SUCCESS,
                "555",
            ),
        ]

        assert caplog.record_tuples == [
            ("app.app", 10, "Incoming event: {'destination': 'test'}"),
            ("app.app", 20, "'test' is a valid and conform SIP."),
        ]

        event_listener.pulsar_client.acknowledge.assert_called_once()

    @patch("app.app.PulsarBinding")
    @patch("app.app.Bag")
    @patch("app.app.EventListener.produce_event")
    @pytest.mark.parametrize(
        "error, bag_error",
        [
            (BagParseError("Not a bag"), "could not be parsed"),
            (BagNotValidError("Not valid"), "is not a valid bag"),
        ],
    )
    def test_handle_incoming_message_bag_not_parsable(
        self,
        produce_event_mock,
        bag_mock,
        pulsar_binding_mock,
        event_listener,
        event,
        error,
        bag_error,
        caplog,
    ):
        # Arrange
        # Return an CloudEvent from a Pulsar message
        pulsar_binding_mock.from_protocol.return_value = event
        # Error when parsing the bag
        bag_mock().parse_validate.side_effect = error

        # Act
        event_listener.handle_incoming_message("")

        # Assert
        assert produce_event_mock.call_count == 1
        assert produce_event_mock.call_args.args == (
            "bag.validate",
            {"message": f"'test' {bag_error}: {str(error)}"},
            "test",
            EventOutcome.FAIL,
            "555",
        )

        assert caplog.record_tuples[1] == (
            "app.app",
            logging.ERROR,
            f"'test' {bag_error}: {str(error)}",
        )

        event_listener.pulsar_client.acknowledge.assert_called_once()

    @patch("app.app.PulsarBinding")
    @patch("app.app.Bag")
    @patch("app.app.EventListener.produce_event")
    @patch("app.app.determine_profile")
    def test_handle_incoming_message_xsd_validation_errors(
        self,
        determine_profile_mock,
        produce_event_mock,
        bag_mock,
        pulsar_binding_mock,
        event_listener,
        event,
        caplog,
    ):
        # Arrange
        # Return an CloudEvent from a Pulsar message
        pulsar_binding_mock.from_protocol.return_value = event
        # Error when validating the metadata
        determine_profile_mock().validate_metadata.return_value = ["Not valid PREMIS"]

        # Act
        event_listener.handle_incoming_message("")

        # Assert
        assert produce_event_mock.call_count == 2
        assert produce_event_mock.call_args.args == (
            "sip.validate.xsd",
            {
                "message": "Metadata files are not valid against XSD",
                "errors": ["Not valid PREMIS"],
            },
            "test",
            EventOutcome.FAIL,
            "555",
        )

        assert caplog.record_tuples[1] == (
            "app.app",
            logging.ERROR,
            "test: Metadata files are not valid against XSD",
        )

        event_listener.pulsar_client.acknowledge.assert_called_once()

    @patch("app.app.PulsarBinding")
    @patch("app.app.Bag")
    @patch("app.app.EventListener.produce_event")
    @patch("app.app.determine_profile")
    def test_handle_incoming_message_parse_graph_error(
        self,
        determine_profile_mock,
        produce_event_mock,
        bag_mock,
        pulsar_binding_mock,
        event_listener,
        event,
        caplog,
    ):
        # Arrange
        # Return an CloudEvent from a Pulsar message
        pulsar_binding_mock.from_protocol.return_value = event
        # There should be no errors when validating the metadata
        determine_profile_mock().validate_metadata.return_value = []
        # There should be a ParseGraphError when parsing the graph.
        determine_profile_mock().parse_graph.side_effect = GraphParseError(
            "Could not parse"
        )

        # Act
        event_listener.handle_incoming_message("")

        # Assert
        assert produce_event_mock.call_count == 3
        assert produce_event_mock.call_args.args == (
            "sip.loadgraph",
            {
                "message": "Cannot transform metadata into a graph.",
                "errors": "Could not parse",
            },
            "test",
            EventOutcome.FAIL,
            "555",
        )

        assert caplog.record_tuples[1] == (
            "app.app",
            logging.ERROR,
            "test: Cannot transform metadata into a graph.",
        )

        event_listener.pulsar_client.acknowledge.assert_called_once()

    @patch("app.app.PulsarBinding")
    @patch("app.app.Bag")
    @patch("app.app.EventListener.produce_event")
    @patch("app.app.determine_profile")
    def test_handle_incoming_message_graph_not_conform_error(
        self,
        determine_profile_mock,
        produce_event_mock,
        bag_mock,
        pulsar_binding_mock,
        event_listener,
        event,
        caplog,
    ):
        # Arrange
        # Return an CloudEvent from a Pulsar message
        pulsar_binding_mock.from_protocol.return_value = event
        # There should be no errors when validating the metadata
        determine_profile_mock().validate_metadata.return_value = []
        # Return JSON serialized in byte format when parsing the graph
        determine_profile_mock().parse_graph().serialize.return_value = (
            b'{"graph": "info"}'
        )
        # There should be a GraphNotConformError when validating the graph
        determine_profile_mock().validate_graph.side_effect = GraphNotConformError(
            "Missing node"
        )
        # Act
        event_listener.handle_incoming_message("")

        # Assert
        assert produce_event_mock.call_count == 4
        assert produce_event_mock.call_args.args == (
            "sip.validate.shacl",
            {
                "message": "Graph is not conform.",
                "errors": "Missing node",
            },
            "test",
            EventOutcome.FAIL,
            "555",
        )

        assert caplog.record_tuples[1] == (
            "app.app",
            logging.ERROR,
            "test: Graph is not conform.",
        )

        event_listener.pulsar_client.acknowledge.assert_called_once()
