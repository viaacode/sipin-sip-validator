from pathlib import Path

import pytest
from rdflib import Graph
from rdflib.compare import isomorphic

from app.models.profile import (
    BasicProfile10,
    BasicProfile11,
    determine_profile,
    MaterialArtworkProfile11,
    XMLNotValidError,
    GraphNotConformError,
)


@pytest.mark.parametrize(
    "path, profile_class",
    [
        (Path("1.0", "basic", "sips", "conform"), BasicProfile10),
        (Path("1.1", "basic", "sips", "conform"), BasicProfile11),
        (
            Path("1.1", "artwork", "sips", "2D_fa307608-35c3-11ed-9243-7e92631d7d27"),
            MaterialArtworkProfile11,
        ),
    ],
)
def test_determine_profile(path, profile_class):
    profile = determine_profile(Path("tests", "resources").joinpath(path))
    assert type(profile) == profile_class


def test_determine_profile_unknown():
    with pytest.raises(ValueError) as e:
        determine_profile(
            Path("tests", "resources", "sips", "other", "unknown_profile")
        )

    assert (
        str(e.value)
        == "Profile not known: https://data.hetarchief.be/id/sip/1.0/unknown."
    )


def test_determine_profile_missing():
    with pytest.raises(ValueError) as e:
        determine_profile(
            Path("tests", "resources", "sips", "other", "missing_profile")
        )

    assert str(e.value) == "METS does not contain a CONTENTINFORMATIONTYPE attribute."


def test_determine_profile_no_mets():
    with pytest.raises(ValueError) as e:
        determine_profile(Path("tests", "resources", "sips", "other", "no_mets"))

    assert "METS could not be parsed: Error reading file" in str(e.value)


def test_determine_profile_corrupt_mets():
    with pytest.raises(ValueError) as e:
        determine_profile(Path("tests", "resources", "sips", "other", "corrupt_mets"))

    assert (
        str(e.value)
        == "METS could not be parsed: Premature end of data in tag mets line 2, line 25, column 11 (mets.xml, line 25)."
    )


class TestBasicProfile10:
    @pytest.fixture
    def profile_conform(self):
        path = Path(
            "tests",
            "resources",
            "1.0",
            "basic",
            "sips",
            "conform",
        )
        return BasicProfile10(path)

    @pytest.fixture
    def profile_conform_extended(self):
        path = Path(
            "tests",
            "resources",
            "1.0",
            "basic",
            "sips",
            "conform_extended",
        )
        return BasicProfile10(path)

    @pytest.fixture
    def profile_invalid_xml(self):
        path = Path(
            "tests",
            "resources",
            "1.0",
            "basic",
            "sips",
            "invalid_xml",
        )
        return BasicProfile10(path)

    @pytest.fixture
    def profile_not_conform(self):
        path = Path(
            "tests",
            "resources",
            "1.0",
            "basic",
            "sips",
            "not_conform",
        )
        return BasicProfile10(path)

    @pytest.fixture
    def profile_empty_graph(self):
        path = Path(
            "tests",
            "resources",
            "1.0",
            "basic",
            "sips",
            "empty_graph",
        )
        return BasicProfile10(path)

    def graph_path(self) -> Path:
        return Path(
            "tests",
            "resources",
            "1.0",
            "basic",
            "graph",
        )

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
            == "Element '{http://www.loc.gov/METS/}mets': Missing child element(s). Expected is ( {http://www.loc.gov/METS/}structMap )., line 2"
        )

        error_2 = errors[1]
        assert type(error_2) == XMLNotValidError
        assert (
            str(error_2)
            == "Element '{http://www.loc.gov/METS/}unknownSpec': This element is not expected. Expected is one of ( {http://www.loc.gov/METS/}dmdSec, {http://www.loc.gov/METS/}amdSec, {http://www.loc.gov/METS/}fileSec, {http://www.loc.gov/METS/}structMap )., line 6"
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
        path = self.graph_path().joinpath(expected_graph_path, "graph.ttl")
        expected.parse(str(path))
        assert isomorphic(graph, expected)

    def test_parse_validate_profile_not_conform(self, profile_not_conform):
        graph = profile_not_conform.parse_graph()
        with pytest.raises(GraphNotConformError):
            profile_not_conform.validate_graph(graph)

    def test_parse_validate_profile_empty_graph(self, profile_empty_graph):
        graph = profile_empty_graph.parse_graph()
        with pytest.raises(GraphNotConformError) as e:
            profile_empty_graph.validate_graph(graph)
        assert (
            str(e.value)
            == "Graph is perceived as empty as it does not contain an intellectual entity."
        )


class TestBasicProfile11(TestBasicProfile10):
    @pytest.fixture
    def profile_conform(self):
        path = Path(
            "tests",
            "resources",
            "1.1",
            "basic",
            "sips",
            "conform",
        )
        return BasicProfile11(path)

    @pytest.fixture
    def profile_conform_extended(self):
        path = Path(
            "tests",
            "resources",
            "1.1",
            "basic",
            "sips",
            "conform_extended",
        )
        return BasicProfile11(path)

    @pytest.fixture
    def profile_conform_batch_id(self):
        path = Path(
            "tests",
            "resources",
            "1.1",
            "basic",
            "sips",
            "conform_batch_id",
        )
        return BasicProfile11(path)

    @pytest.fixture
    def profile_invalid_xml(self):
        path = Path(
            "tests",
            "resources",
            "1.1",
            "basic",
            "sips",
            "invalid_xml",
        )
        return BasicProfile11(path)

    @pytest.fixture
    def profile_not_conform(self):
        path = Path(
            "tests",
            "resources",
            "1.1",
            "basic",
            "sips",
            "not_conform",
        )
        return BasicProfile11(path)

    @pytest.fixture
    def profile_empty_graph(self):
        path = Path(
            "tests",
            "resources",
            "1.1",
            "basic",
            "sips",
            "empty_graph",
        )
        return BasicProfile11(path)

    def graph_path(self) -> Path:
        return Path(
            "tests",
            "resources",
            "1.1",
            "basic",
            "graph",
        )

    @pytest.mark.parametrize(
        "profile_name, expected_graph_path",
        [
            ("profile_conform", "conform"),
            ("profile_conform_extended", "conform_extended"),
            ("profile_conform_batch_id", "conform_batch_id"),
        ],
    )
    def test_parse_validate_graph(self, profile_name, expected_graph_path, request):
        profile = request.getfixturevalue(profile_name)
        graph = profile.parse_graph()
        # Check if valid
        assert profile.validate_graph(graph)

        # Check if expected
        expected = Graph()
        path = self.graph_path().joinpath(expected_graph_path, "graph.ttl")
        expected.parse(str(path))
        assert isomorphic(graph, expected)


class TestMaterialArtworkProfile11:
    def graph_path(self) -> Path:
        return Path(
            "tests",
            "resources",
            "1.1",
            "artwork",
            "graph",
        )

    @pytest.fixture
    def profile_2D(self):
        path = Path(
            "tests",
            "resources",
            "1.1",
            "artwork",
            "sips",
            "2D_fa307608-35c3-11ed-9243-7e92631d7d27",
        )
        return MaterialArtworkProfile11(path)

    @pytest.fixture
    def profile_3D(self):
        path = Path(
            "tests",
            "resources",
            "1.1",
            "artwork",
            "sips",
            "3D_3d4bd7ca-38c6-11ed-95f2-7e92631d7d28",
        )
        return MaterialArtworkProfile11(path)

    @pytest.fixture
    def minimal(self):
        path = Path(
            "tests",
            "resources",
            "1.1",
            "artwork",
            "sips",
            "minimal",
        )
        return MaterialArtworkProfile11(path)

    @pytest.fixture
    def minimal_meemoo_batch_id(self):
        path = Path(
            "tests",
            "resources",
            "1.1",
            "artwork",
            "sips",
            "minimal_meemoo_batch_id",
        )
        return MaterialArtworkProfile11(path)

    @pytest.mark.parametrize(
        "profile_name",
        ["profile_2D", "profile_3D"],
    )
    def test_validate_premis(self, profile_name, request):
        profile = request.getfixturevalue(profile_name)
        errors = profile._validate_premis()

        assert not errors

    @pytest.mark.parametrize(
        "profile_name",
        ["profile_2D", "profile_3D"],
    )
    def test_validate_mets(self, profile_name, request):
        profile = request.getfixturevalue(profile_name)
        errors = profile._validate_mets()

        assert not errors

    @pytest.mark.parametrize(
        "profile_name",
        ["profile_2D", "profile_3D", "minimal"],
    )
    def test_validate_descriptive(self, profile_name, request):
        profile = request.getfixturevalue(profile_name)
        errors = profile._validate_descriptive()

        assert not errors

    @pytest.mark.parametrize(
        "profile_name",
        ["profile_2D", "profile_3D", "minimal"],
    )
    def test_validate_metadata(self, profile_name, request):
        profile = request.getfixturevalue(profile_name)
        errors = profile.validate_metadata()

        assert not errors

    @pytest.mark.parametrize(
        "profile_name, expected_graph_path",
        [
            ("profile_2D", "2D_fa307608-35c3-11ed-9243-7e92631d7d27"),
            ("profile_3D", "3D_3d4bd7ca-38c6-11ed-95f2-7e92631d7d28"),
            ("minimal", "minimal"),
            ("minimal_meemoo_batch_id", "minimal_meemoo_batch_id"),
        ],
    )
    def test_parse_validate_graph(self, profile_name, expected_graph_path, request):
        profile = request.getfixturevalue(profile_name)

        graph = profile.parse_graph()
        # Check if valid
        assert profile.validate_graph(graph)

        # Check if expected
        expected = Graph()
        path = self.graph_path().joinpath(expected_graph_path, "graph.ttl")
        expected.parse(str(path))
        assert isomorphic(graph, expected)
