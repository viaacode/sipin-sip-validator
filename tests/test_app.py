from pathlib import Path
from unittest.mock import patch

import pytest

from app.app import EventListener
from app.models.profile import BasicProfile


class TestEventListener:
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
