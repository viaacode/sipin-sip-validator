from abc import ABC, abstractmethod
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from lxml import etree
from rdflib import Graph, URIRef
from pyshacl import validate as shacl_validate
from pysparql_anything import SparqlAnything

from app.models.profiles.exceptions import (
    GraphNotConformError,
    XMLNotValidError,
)

sa = SparqlAnything()


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
    def query_descriptive_ie() -> Path:
        pass

    @staticmethod
    @abstractmethod
    def query_premis_ie() -> Path:
        pass

    @staticmethod
    @abstractmethod
    def query_premis_representation() -> Path:
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

    def _validate_premis(self) -> list[XMLNotValidError]:
        """Validate the PREMIS files.

        There are multiple premis files, one on the package level and
        one for each representation.

        Returns:
            A list with errors detailing the parse/validation errors.
        """
        errors = []

        premis_xsd = etree.XMLSchema(etree.parse(self.premis_xsd()))

        premis_package_path: Path = self.bag_path.joinpath(
            "data", "metadata", "preservation", "premis.xml"
        )

        # PREMIS on package level
        try:
            premis_package = etree.parse(premis_package_path)
            premis_xsd.assertValid(premis_package)
        except (etree.DocumentInvalid, etree.ParseError) as e:
            errors.append(XMLNotValidError(str(e.error_log)))

        # PREMIS on representation level
        for premis_representation_path in self.bag_path.glob(
            str(
                Path(
                    "data",
                    "representations",
                    "representation_*",
                    "metadata",
                    "preservation",
                    "premis.xml",
                )
            )
        ):
            try:
                premis_representation = etree.parse(premis_representation_path)
                premis_xsd.assertValid(premis_representation)
            except (etree.DocumentInvalid, etree.ParseError) as e:
                errors.append(XMLNotValidError(str(e.error_log)))

        return errors

    def _validate_mets(self) -> list[XMLNotValidError]:
        """Validate the METS files.

        There are multiple METS files, one on the package level and one for
        every representation.

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
            errors.append(XMLNotValidError(str(e.error_log)))

        # METS on representation level
        for mets_representation_path in self.bag_path.glob(
            str(Path("data", "representations", "representation_*", "mets.xml"))
        ):
            try:
                mets_representation = etree.parse(mets_representation_path)
                mets_xsd.assertValid(mets_representation)
            except (etree.DocumentInvalid, etree.ParseError) as e:
                errors.append(XMLNotValidError(str(e.error_log)))

        return errors

    def validate_metadata(self) -> list[XMLNotValidError]:
        """Validate the metadata files.

        A profile has:
            - Multiple METS files (package and one per representation level).
            - Multiple PREMIS files (package one per and representation level).
            - One or more descriptive metadata file (one on package and possible
              one per representation level).

        Returns:
            A list with errors detailing the parse/validation errors.
        """
        errors: list = self._validate_premis()
        errors.extend(self._validate_mets())
        errors.extend(self._validate_descriptive())

        return errors

    @abstractmethod
    def _validate_descriptive(self) -> list[XMLNotValidError]:
        """Validate the descriptive metadata.

        Returns:
            A list with errors detailing the parse/validation errors.
        """
        pass

    @abstractmethod
    def _construct_shacl_graph(self) -> Graph:
        """Construct a graph containing the SHACLs.

        This is used for validating the data graph.

        Returns:
            A SHACL graph.
        """

        pass

    def validate_graph(self, data_graph: Graph) -> bool:
        """Validate if the graph is conform.

        Returns: True if the graph was conform.

        Raises:
            GraphNotConformError: If not conform, containing the reason why.
        """
        # An empty graph conforms with the SHACL. Check if the graph has at least
        # a premis:intellectualEntity node.
        if (
            None,
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
            URIRef("http://www.loc.gov/premis/rdf/v3/IntellectualEntity"),
        ) not in data_graph:
            raise GraphNotConformError(
                "Graph is perceived as empty as it does not contain an intellectual entity."
            )
        shacl_graph = self._construct_shacl_graph()
        conforms, results_graph, results_text = shacl_validate(
            data_graph=data_graph,
            shacl_graph=shacl_graph,
            meta_shacl=True,
            allow_warnings=True,
        )

        if not conforms:
            raise GraphNotConformError(results_text)

        return True
