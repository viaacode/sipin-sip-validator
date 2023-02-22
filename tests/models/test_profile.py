from pathlib import Path

import pytest
from rdflib import Graph
from rdflib.compare import isomorphic

from app.models.profile import BasicProfile, XMLNotValidError, GraphNotConformError


class TestBasicProfile:
    @pytest.fixture
    def profile_conform(self):
        path = Path(
            "tests",
            "resources",
            "sips",
            "basic",
            "conform",
        )
        return BasicProfile(path)

    @pytest.fixture
    def profile_conform_extended(self):
        path = Path(
            "tests",
            "resources",
            "sips",
            "basic",
            "conform_extended",
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

    @pytest.fixture
    def profile_empty_graph(self):
        path = Path(
            "tests",
            "resources",
            "sips",
            "other",
            "empty_graph",
        )
        return BasicProfile(path)

    @pytest.mark.parametrize(
        "profile_name",
        ["profile_conform", "profile_conform_extended"],
    )
    def test_validate_premis(self, profile_name, request):
        profile = request.getfixturevalue(profile_name)
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

    @pytest.mark.parametrize(
        "profile_name",
        ["profile_conform", "profile_conform_extended"],
    )
    def test_validate_dcterms(self, profile_name, request):
        profile = request.getfixturevalue(profile_name)
        error = profile._validate_dcterms()

        assert not error

    def test_validate_dcterms_not_valid(self, profile_invalid_xml):
        error = profile_invalid_xml._validate_dcterms()

        assert error

    @pytest.mark.parametrize(
        "profile_name",
        ["profile_conform", "profile_conform_extended"],
    )
    def test_validate_mets(self, profile_name, request):
        profile = request.getfixturevalue(profile_name)
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

    @pytest.mark.parametrize(
        "profile_name",
        ["profile_conform", "profile_conform_extended"],
    )
    def test_validate_metadata(self, profile_name, request):
        profile = request.getfixturevalue(profile_name)
        errors = profile.validate_metadata()

        assert not errors

    def test_validate_metadata_not_valid(self, profile_invalid_xml):
        errors = profile_invalid_xml.validate_metadata()

        assert errors

    @pytest.mark.parametrize(
        "profile_name, expected_graph_path",
        [
            ("profile_conform", "conform"),
            ("profile_conform_extended", "conform_extended"),
        ],
    )
    def test_parse_validate_graph(self, profile_name, expected_graph_path, request):
        profile = request.getfixturevalue(profile_name)
        graph = profile.parse_graph()
        # Check if valid
        assert profile.validate_graph(graph)

        # Check if expected
        expected = Graph()
        expected.parse(f"tests/resources/graph/basic/{expected_graph_path}/graph.ttl")
        assert isomorphic(graph, expected)

    def test_parse_validate_profile_not_conform(self, profile_not_conform):
        graph = profile_not_conform.parse_graph()
        with pytest.raises(GraphNotConformError):
            profile_not_conform.validate_graph(graph)

    def test_parse_validate_profile_empty_graph(self, profile_empty_graph):
        graph = profile_empty_graph.parse_graph()
        with pytest.raises(GraphNotConformError) as e:
            profile_empty_graph.validate_graph(graph)
        assert str(e.value) == "Empty graph"
