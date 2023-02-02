from pathlib import Path

import pytest

from app.models.bag import Bag, BagNotValidError, BagParseError


class TestBag:
    @pytest.fixture
    def bag(self):
        path = Path(
            "tests",
            "resources",
            "bags",
            "valid",
        )
        return Bag(path)

    @pytest.fixture
    def bag_invalid(self):
        path = Path(
            "tests",
            "resources",
            "bags",
            "invalid_bag",
        )
        return Bag(path)

    @pytest.fixture
    def not_a_bag(self):
        path = Path(
            "tests",
            "resources",
            "bags",
            "not_a_bag",
        )
        return Bag(path)

    def test_parse_validate(self, bag):
        assert bag.parse_validate()

    def test_parse_validate_invalid(self, bag_invalid):
        with pytest.raises(BagNotValidError) as e:
            bag_invalid.parse_validate()

        assert (
            str(e.value)
            == "Payload-Oxum validation failed. Expected 1 files and 0 bytes but found 2 files and 9 bytes"
        )

    def test_parse_validate_parse_error(self, not_a_bag):
        with pytest.raises(BagParseError) as e:
            not_a_bag.parse_validate()

        assert "Expected bagit.txt does not exist" in str(e.value)
