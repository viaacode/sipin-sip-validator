import subprocess
from pathlib import Path

from lxml import etree
from rdflib import Graph
from pyshacl import validate as shacl_validate


SPARQL_ANYTHING_JAR: Path = Path("app", "resources", "sparql-anything-0.8.1.jar")
QUERY_BASIC: Path = Path("app", "resources", "sparql", "basic.sparql")
SHACL_BASIC: Path = Path("app", "resources", "shacl", "basic.shacl")


PREMIS_XSD: Path = Path("app", "resources", "xsd", "premis-v3-0.xsd")
METS_XSD: Path = Path("app", "resources", "xsd", "mets.xsd")
DCTERMS_XSD: Path = Path("app", "resources", "xsd", "dcterms.xsd")


class XMLNotValidError(Exception):
    pass


class GraphParseError(Exception):
    pass


class GraphNotConformError(Exception):
    pass


class Profile:
    def __init__(self, bag_path: Path):
        self.bag_path = bag_path


class BasicProfile(Profile):
    def _validate_premis(self) -> list[XMLNotValidError]:
        """Validate the PREMIS files.

        Basic profile has two premis files, one on the package level and
        one on the representation level.

        Returns:
            A list with errors detailing the parse/validation errors.
        """
        premis_xsd = etree.XMLSchema(etree.parse(PREMIS_XSD))

        premis_package_path: Path = self.bag_path.joinpath(
            "data", "metadata", "preservation", "premis.xml"
        )
        premis_representation_path: Path = self.bag_path.joinpath(
            "data",
            "representations",
            "representation_1",
            "metadata",
            "preservation",
            "premis.xml",
        )

        errors = []
        # PREMIS on package level
        try:
            premis_package = etree.parse(premis_package_path)
            premis_xsd.assertValid(premis_package)
        except (etree.DocumentInvalid, etree.ParseError) as e:
            errors.append(XMLNotValidError(str(e)))

        # PREMIS on representation level
        try:
            premis_representation = etree.parse(premis_representation_path)
            premis_xsd.assertValid(premis_representation)
        except (etree.DocumentInvalid, etree.ParseError) as e:
            errors.append(XMLNotValidError(str(e)))

        return errors

    def _validate_dcterms(self) -> XMLNotValidError | None:
        """Validate the dcterms file.

        Basic profile has one file with the descriptive metadata.

        Returns:
            A parse/validation error if applicable.
        """
        dcterms_xsd = etree.XMLSchema(etree.parse(PREMIS_XSD))

        dcterms_package_path: Path = self.bag_path.joinpath(
            "data", "metadata", "preservation", "premis.xml"
        )
        dcterms_package_path: Path = self.bag_path.joinpath(
            "data",
            "metadata",
            "descriptive",
            "dc_1.xml",
        )

        # DCTERMS on package level
        try:
            dcterms_package = etree.parse(dcterms_package_path)
            dcterms_xsd.assertValid(dcterms_package)
        except (etree.DocumentInvalid, etree.ParseError) as e:
            error = XMLNotValidError(str(e))

        return error

    def _validate_mets(self) -> list[XMLNotValidError]:
        """Validate the METS files.

        Basic profile has two METS files, one on the package level and one on
        the representation level.

        Returns:
            A list with errors detailing the parse/validation errors.
        """

        mets_xsd = etree.XMLSchema(etree.parse(METS_XSD))

        mets_package_path: Path = self.bag_path.joinpath("data", "mets.xml")
        mets_representation_path: Path = self.bag_path.joinpath(
            "data", "representations", "representation_1", "mets.xml"
        )

        errors = []
        # METS on package level
        try:
            mets_package = etree.parse(mets_package_path)
            mets_xsd.assertValid(mets_package)
        except (etree.DocumentInvalid, etree.ParseError) as e:
            errors.append(XMLNotValidError(str(e)))

        # METS on representation level
        try:
            mets_representation = etree.parse(mets_representation_path)
            mets_xsd.assertValid(mets_representation)
        except (etree.DocumentInvalid, etree.ParseError) as e:
            errors.append(XMLNotValidError(str(e)))

        return errors

    def validate_metadata(self) -> list[XMLNotValidError]:
        """Validate the metadata files.

        Basic profile has:
            - Two METS files (package and representation level).
            - Two PREMIS files (package and representation level).
            - One descriptive metadata file (dcterms).

        Returns:
            A list with errors detailing the parse/validation errors.
        """
        errors: list = self._validate_premis()
        errors.extend(self._validate_mets())
        result = self._validate_dcterms()
        if result:
            errors.append(result)

        return errors

    def parse_graph(self) -> Graph:
        """Parse the metadata as a graph.

        Transform the metadata to rdf and then load it into a graph.

        Returns:
            The graph.
        Raises:
            GraphParseError: If parsing failed.
        """
        try:
            output = subprocess.run(
                [
                    "java",
                    "-jar",
                    str(SPARQL_ANYTHING_JAR),
                    "-q",
                    str(QUERY_BASIC),
                ],
                capture_output=True,
                check=True,
                universal_newlines=True,
            )
        except subprocess.CalledProcessError as e:
            raise GraphParseError(f"Error when parsing graph: {str(e)}")

        data_graph = Graph()
        data_graph.parse(data=output.stdout, format="turtle")
        return data_graph

    def validate_graph(self, data_graph: Graph):
        """Validate if the graph is conform

        Raises:
            GraphNotConformError: If not conform, containing the reason why.
        """
        shacl_graph = Graph()
        shacl_graph.parse(str(SHACL_BASIC), format="turtle")
        conforms, results_graph, results_text = shacl_validate(
            data_graph=data_graph,
            shacl_graph=shacl_graph,
        )

        if not conforms:
            raise GraphNotConformError(results_text)
