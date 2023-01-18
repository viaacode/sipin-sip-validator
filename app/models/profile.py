import subprocess
from pathlib import Path

from lxml import etree
from rdflib import Graph

SPARQL_ANYTHING_JAR: Path = Path("app", "resources", "sparql-anything-0.8.1.jar")
QUERY_BASIC: Path = Path("app", "resources", "sparql", "basic.sparql")

PREMIS_XSD: Path = Path("app", "resources", "xsd", "premis-v3-0.xsd")
METS_XSD: Path = Path("app", "resources", "xsd", "mets.xsd")
DCTERMS_XSD: Path = Path("app", "resources", "xsd", "dcterms.xsd")


class XMLNotValidError(Exception):
    pass


class GraphParseError(Exception):
    pass


class Profile:
    def __init__(self, bag_path: Path):
        self.bag_path = bag_path


class BasicProfile(Profile):
    def validate_premis(self):
        """Validate the PREMIS files.

        Basic profile has two premis files, one on the package level and
        one on the representation level.

        Raise:
            XMLNotValidError: If the PREMIS file cannot be parsed or does not
            validate against its XSD.
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

        # PREMIS on package level
        try:
            premis_package = etree.parse(premis_package_path)
        except etree.ParseError as e:
            raise XMLNotValidError(str(e))

        try:
            premis_xsd.assertValid(premis_package)
        except etree.DocumentInvalid as e:
            raise XMLNotValidError(str(e))

        # PREMIS on representation level
        try:
            premis_representation = etree.parse(premis_representation_path)
        except etree.ParseError as e:
            raise XMLNotValidError(str(e))

        try:
            premis_xsd.assertValid(premis_representation)
        except etree.DocumentInvalid as e:
            raise XMLNotValidError(str(e))

    def validate_dcterms(self):
        """Validate the dcterms file.

        Basic profile has one file with the descriptive metadata.

        Raise:
            XMLNotValidError: If the dcterms file cannot be parsed or does not
            validate against its XSD.
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
        except etree.ParseError as e:
            raise XMLNotValidError(str(e))

        try:
            dcterms_xsd.assertValid(dcterms_package)
        except etree.DocumentInvalid as e:
            raise XMLNotValidError(str(e))

    def validate_mets(self):
        """Validate the METS files.

        Basic profile has two METS files, one on the package level and one on
        the representation level.

        Raise:
            XMLNotValidError: If the METS file cannot be parsed or does not
            validate against its XSD.
        """

        mets_xsd = etree.XMLSchema(etree.parse(METS_XSD))

        mets_package_path: Path = self.bag_path.joinpath("data", "mets.xml")
        mets_representation_path: Path = self.bag_path.joinpath(
            "data", "representations", "representation_1", "mets.xml"
        )

        # METS on package level
        try:
            mets_package = etree.parse(mets_package_path)
        except etree.ParseError as e:
            raise XMLNotValidError(str(e))

        try:
            mets_xsd.assertValid(mets_package)
        except etree.DocumentInvalid as e:
            raise XMLNotValidError(str(e))

        # METS on representation level
        try:
            mets_representation = etree.parse(mets_representation_path)
        except etree.ParseError as e:
            raise XMLNotValidError(str(e))
        try:
            mets_xsd.assertValid(mets_representation)
        except etree.DocumentInvalid as e:
            raise XMLNotValidError(str(e))

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

    def handle(self):
        # Validate XML files to XSD
        self.validate_premis()
        self.validate_dcterms()
        self.validate_mets()

        # Parse to graph
        data_graph = self.parse_graph()
