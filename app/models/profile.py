from abc import ABC, abstractmethod
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

from lxml import etree
from rdflib import Graph, URIRef
from pyshacl import validate as shacl_validate
from pysparql_anything import SparqlAnything


NAMESPACES = {
    "mets": "http://www.loc.gov/METS/",
    "csip": "https://DILCIS.eu/XML/METS/CSIPExtensionMETS",
}


class XMLNotValidError(Exception):
    pass


class GraphParseError(Exception):
    pass


class GraphNotConformError(Exception):
    pass


class Profile(ABC):
    def __init__(self, bag_path: Path):
        self.bag_path = bag_path
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.query_sip().parent),
            autoescape=select_autoescape(),
        )

    @staticmethod
    @abstractmethod
    def query_sip() -> Path:
        pass

    @staticmethod
    @abstractmethod
    def query_profile() -> Path:
        pass

    @staticmethod
    @abstractmethod
    def shacl_sip() -> Path:
        pass

    @staticmethod
    @abstractmethod
    def shacl_profile() -> Path:
        pass

    @staticmethod
    @abstractmethod
    def profile_name() -> str:
        """The name of the profile, as defined in the SIP spec."""
        pass


class BasicProfile10(Profile):
    def profile_name() -> str:
        return "https://data.hetarchief.be/id/sip/1.0/basic"

    @staticmethod
    def query_sip() -> Path:
        return Path(
            "app",
            "resources",
            "1.0",
            "basic",
            "sparql",
            "sip.sparql",
        )

    @staticmethod
    def query_profile() -> Path:
        return Path(
            "app",
            "resources",
            "1.0",
            "basic",
            "sparql",
            "basic.sparql",
        )

    @staticmethod
    def shacl_sip() -> Path:
        return Path(
            "app",
            "resources",
            "1.0",
            "basic",
            "shacl",
            "sip.shacl.ttl",
        )

    @staticmethod
    def shacl_profile() -> Path:
        return Path(
            "app",
            "resources",
            "1.0",
            "basic",
            "shacl",
            "basic.shacl.ttl",
        )

    @staticmethod
    def premis_xsd() -> Path:
        return Path(
            "app",
            "resources",
            "1.0",
            "basic",
            "xsd",
            "premis-v3-0.xsd",
        )

    @staticmethod
    def mets_xsd() -> Path:
        return Path(
            "app",
            "resources",
            "1.0",
            "basic",
            "xsd",
            "mets.xsd",
        )

    @staticmethod
    def dcterms_xsd() -> Path:
        return Path(
            "app",
            "resources",
            "1.0",
            "basic",
            "xsd",
            "dc_basic.xsd",
        )

    def _validate_premis(self) -> list[XMLNotValidError]:
        """Validate the PREMIS files.

        Basic profile has two premis files, one on the package level and
        one on the representation level.

        Returns:
            A list with errors detailing the parse/validation errors.
        """
        premis_xsd = etree.XMLSchema(etree.parse(self.premis_xsd()))

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
        dcterms_xsd = etree.XMLSchema(etree.parse(self.dcterms_xsd()))

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

        return None

    def _validate_mets(self) -> list[XMLNotValidError]:
        """Validate the METS files.

        Basic profile has two METS files, one on the package level and one on
        the representation level.

        Returns:
            A list with errors detailing the parse/validation errors.
        """
        mets_xsd = etree.XMLSchema(etree.parse(self.mets_xsd()))

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

        As the SPARQL service paths are dynamic, we need to instantiate
        the SPARQL file and write it in the bag folder.

        Transform the metadata to rdf and then load it into a graph.

        Returns:
            The graph.
        Raises:
            GraphParseError: If parsing failed.
        """
        # write SPARQL-anything query for the SIP.
        query_sip_destination = self.bag_path.joinpath(self.query_sip().name)
        sip_template = self.jinja_env.get_template(str(self.query_sip().name))
        with open(str(query_sip_destination), "w") as f:
            f.write(sip_template.render(bag_path=self.bag_path))

        # write SPARQL-anything query for the BASIC profile.
        query_basic_destination = self.bag_path.joinpath(self.query_profile().name)
        profile_template = self.jinja_env.get_template(str(self.query_profile().name))
        with open(str(query_basic_destination), "w") as f:
            f.write(profile_template.render(bag_path=self.bag_path))

        # Run SPARQL-anything transformation.
        sa = SparqlAnything()
        try:
            sip_graph = sa.construct(q=str(query_sip_destination), f="TTL")
            profile_graph = sa.construct(q=str(query_basic_destination), f="TTL")
            data_graph = sip_graph + profile_graph

        except Exception as e:
            raise GraphParseError(f"Error when parsing graph: {str(e)}")

        return data_graph

    def validate_graph(self, data_graph: Graph) -> bool:
        """Validate if the graph is conform.

        Returns: True if the graph was conform.

        Raises:
            GraphNotConformError: If not conform, containing the reason why.
        """
        # An empty graph conforms with the SHACL. Check if the graph has at least
        # a premis:intellecutalEntity node.
        if (
            None,
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
            URIRef("http://www.loc.gov/premis/rdf/v3/IntellectualEntity"),
        ) not in data_graph:
            raise GraphNotConformError(
                "Graph is perceived as empty as it does not contain an intellectual entity."
            )
        print(data_graph.serialize())
        shacl_graph = Graph()
        shacl_graph.parse(str(self.shacl_sip()), format="turtle")
        shacl_graph.parse(str(self.shacl_profile()), format="turtle")
        conforms, results_graph, results_text = shacl_validate(
            data_graph=data_graph, shacl_graph=shacl_graph, meta_shacl=True
        )

        if not conforms:
            raise GraphNotConformError(results_text)

        return True


class BasicProfile11(BasicProfile10):
    def profile_name() -> str:
        return "https://data.hetarchief.be/id/sip/1.1/basic"

    @staticmethod
    def query_sip() -> Path:
        return Path(
            "app",
            "resources",
            "1.1",
            "basic",
            "sparql",
            "sip.sparql",
        )

    @staticmethod
    def query_profile() -> Path:
        return Path(
            "app",
            "resources",
            "1.1",
            "basic",
            "sparql",
            "basic.sparql",
        )

    @staticmethod
    def shacl_sip() -> Path:
        return Path(
            "app",
            "resources",
            "1.1",
            "basic",
            "shacl",
            "sip.shacl.ttl",
        )

    @staticmethod
    def shacl_profile() -> Path:
        return Path(
            "app",
            "resources",
            "1.1",
            "basic",
            "shacl",
            "basic.shacl.ttl",
        )

    @staticmethod
    def premis_xsd() -> Path:
        return Path(
            "app",
            "resources",
            "1.1",
            "basic",
            "xsd",
            "premis-v3-0.xsd",
        )

    @staticmethod
    def mets_xsd() -> Path:
        return Path(
            "app",
            "resources",
            "1.1",
            "basic",
            "xsd",
            "mets.xsd",
        )

    @staticmethod
    def dcterms_xsd() -> Path:
        return Path(
            "app",
            "resources",
            "1.1",
            "basic",
            "xsd",
            "dc_basic.xsd",
        )


def determine_profile(path: Path) -> Profile:
    """Parse the root METS in order to determine the profile.

    Returns:
        The instantiated Profile
    Raises:
        ValueError:
            - If the package METS could not be parsed.
            - If there is no profile information in the package METS.
            - If the profile is not known.
    """
    try:
        root = etree.parse(path.joinpath("data", "mets.xml"))
    except (etree.ParseError, OSError) as e:
        raise ValueError(f"METS could not be parsed: {e}.")

    # Parse the meemoo profile in the IE METS
    try:
        profile_type = root.xpath(
            "/mets:mets/@csip:CONTENTINFORMATIONTYPE",
            namespaces=NAMESPACES,
        )[0]
    except IndexError:
        raise ValueError("METS does not contain a CONTENTINFORMATIONTYPE attribute.")

    if profile_type == BasicProfile10.profile_name():
        return BasicProfile10(path)
    if profile_type == BasicProfile11.profile_name():
        return BasicProfile11(path)
    raise ValueError(f"Profile not known: {profile_type}.")
