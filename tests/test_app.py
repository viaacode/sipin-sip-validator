from pathlib import Path
from unittest.mock import patch

import pytest
from cloudevents.events import EventOutcome

from app.app import EventListener
from app.models.profile import BasicProfile
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

    def test_determine_profile_basic(self, event_listener):
        profile = event_listener.determine_profile(
            Path("tests", "resources", "sips", "basic", "conform")
        )
        assert type(profile) == BasicProfile

    def test_determine_profile_unknown(self, event_listener):

        with pytest.raises(ValueError) as e:
            event_listener.determine_profile(
                Path("tests", "resources", "sips", "other", "unknown_profile")
            )

        assert (
            str(e.value)
            == "Profile not known: https://data.hetarchief.be/id/sip/1.0/unknown."
        )

    def test_determine_profile_missing(self, event_listener):
        with pytest.raises(ValueError) as e:
            event_listener.determine_profile(
                Path("tests", "resources", "sips", "other", "missing_profile")
            )

        assert (
            str(e.value) == "METS does not contain a CONTENTINFORMATIONTYPE attribute."
        )

    def test_determine_profile_no_mets(self, event_listener):
        with pytest.raises(ValueError) as e:
            event_listener.determine_profile(
                Path("tests", "resources", "sips", "other", "no_mets")
            )

        assert "METS could not be parsed: Error reading file" in str(e.value)

    def test_determine_profile_corrupt_mets(self, event_listener):
        with pytest.raises(ValueError) as e:
            event_listener.determine_profile(
                Path("tests", "resources", "sips", "other", "corrupt_mets")
            )

        assert (
            str(e.value)
            == "METS could not be parsed: Premature end of data in tag mets line 2, line 25, column 11 (mets.xml, line 25)."
        )

    @patch("app.app.PulsarBinding")
    @patch("app.app.Bag")
    @patch("app.app.EventListener.produce_event")
    @patch("app.app.EventListener.determine_profile")
    def test_handle_incoming_message(
        self,
        determine_profile_mock,
        produce_event_mock,
        bag_mock,
        pulsar_binding_mock,
        event_listener,
        event,
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
            {"message": f"test {bag_error}: {str(error)}"},
            "test",
            EventOutcome.FAIL,
            "555",
        )

        event_listener.pulsar_client.acknowledge.assert_called_once()
