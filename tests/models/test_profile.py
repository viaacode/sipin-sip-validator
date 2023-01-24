from pathlib import Path

import pytest

from app.models.profile import BasicProfile, XMLNotValidError, GraphNotConformError


class TestBasicProfile:
    @pytest.fixture
    def profile(self):
        path = Path(
            "tests",
            "resources",
            "sips",
            "basic",
            "conform",
        )
        return BasicProfile(path)

    @pytest.fixture
    def profile_invalid_xml(self):
        path = Path(
            "tests",
            "resources",
            "sips",
            "basic",
            "invalid_xml",
        )
        return BasicProfile(path)

    @pytest.fixture
    def profile_not_conform(self):
        path = Path(
            "tests",
            "resources",
            "sips",
            "basic",
            "not_conform",
        )
        return BasicProfile(path)

    def test_validate_premis(self, profile):
        errors = profile._validate_premis()

        assert not errors

    def test_validate_premis_not_valid(self, profile_invalid_xml):
        errors = profile_invalid_xml._validate_premis()

        assert len(errors) == 2
        error_1 = errors[0]
        assert type(error_1) == XMLNotValidError
        assert (
            str(error_1)
            == "Element '{http://www.loc.gov/premis/v3}relationship': This element is not expected. Expected is ( {http://www.loc.gov/premis/v3}objectIdentifier )., line 10"
        )

        error_2 = errors[1]
        assert type(error_2) == XMLNotValidError
        assert (
            str(error_2)
            == "Element '{http://www.loc.gov/premis/v3}objectCharacteristics': Missing child element(s). Expected is ( {http://www.loc.gov/premis/v3}format )., line 49"
        )

    def test_validate_dcterms(self, profile):
        error = profile._validate_dcterms()

        assert not error

    def test_validate_dcterms_not_valid(self, profile_invalid_xml):
        error = profile_invalid_xml._validate_dcterms()

        assert error

    def test_validate_mets(self, profile):
        errors = profile._validate_mets()

        assert not errors

    def test_validate_mets_not_valid(self, profile_invalid_xml):
        errors = profile_invalid_xml._validate_mets()

        assert len(errors) == 2
        error_1 = errors[0]
        assert type(error_1) == XMLNotValidError
        assert (
            str(error_1)
            == "Element '{http://www.loc.gov/METS/}mets': Missing child element(s). Expected is ( {http://www.loc.gov/METS/}structMap )., line 7"
        )

        error_2 = errors[1]
        assert type(error_2) == XMLNotValidError
        assert (
            str(error_2)
            == "Element '{http://www.loc.gov/METS/}unknownSpec': This element is not expected. Expected is one of ( {http://www.loc.gov/METS/}dmdSec, {http://www.loc.gov/METS/}amdSec, {http://www.loc.gov/METS/}fileSec, {http://www.loc.gov/METS/}structMap )., line 10"
        )

    def test_validate_metadata(self, profile):
        errors = profile.validate_metadata()

        assert not errors

    def test_validate_metadata_not_valid(self, profile_invalid_xml):
        errors = profile_invalid_xml.validate_metadata()

        assert errors

    def test_parse_validate_graph(self, profile):
        graph = profile.parse_graph()
        assert profile.validate_graph(graph)

    def test_parse_validate_profile_not_conform(self, profile_not_conform):
        graph = profile_not_conform.parse_graph()
        with pytest.raises(GraphNotConformError):
            profile_not_conform.validate_graph(graph)
