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
    def query_descriptive_ie() -> Path:
        return Path(
            "app",
            "resources",
            "1.0",
            "basic",
            "sparql",
            "descriptive_ie.sparql",
        )

    @staticmethod
    def query_premis_ie() -> Path:
        return Path(
            "app",
            "resources",
            "1.0",
            "basic",
            "sparql",
            "premis_ie.sparql",
        )

    @staticmethod
    def query_premis_representation() -> Path:
        return Path(
            "app",
            "resources",
            "1.0",
            "basic",
            "sparql",
            "premis_representation.sparql",
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
            errors.append(XMLNotValidError(str(e.error_log)))

        # PREMIS on representation level
        try:
            premis_representation = etree.parse(premis_representation_path)
            premis_xsd.assertValid(premis_representation)
        except (etree.DocumentInvalid, etree.ParseError) as e:
            errors.append(XMLNotValidError(str(e.error_log)))

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
            error = XMLNotValidError(str(e.error_log))
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
            errors.append(XMLNotValidError(str(e.error_log)))

        # METS on representation level
        try:
            mets_representation = etree.parse(mets_representation_path)
            mets_xsd.assertValid(mets_representation)
        except (etree.DocumentInvalid, etree.ParseError) as e:
            errors.append(XMLNotValidError(str(e.error_log)))

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

        # write SPARQL-anything query for the descriptive metadata on IE level.
        query_descriptive_ie_destination = self.bag_path.joinpath(
            self.query_descriptive_ie().name
        )
        profile_template = self.jinja_env.get_template(
            str(self.query_descriptive_ie().name)
        )
        with open(str(query_descriptive_ie_destination), "w") as f:
            f.write(profile_template.render(bag_path=self.bag_path))

        # write SPARQL-anything query for the premis metadata on the IE level.
        query_premis_ie_destination = self.bag_path.joinpath(
            self.query_premis_ie().name
        )
        profile_template = self.jinja_env.get_template(str(self.query_premis_ie().name))
        with open(str(query_premis_ie_destination), "w") as f:
            f.write(profile_template.render(bag_path=self.bag_path))

        # write SPARQL-anything query for the premis metadata on the representation level.
        query_premis_rep_destination = self.bag_path.joinpath(
            self.query_premis_representation().name
        )
        profile_template = self.jinja_env.get_template(
            str(self.query_premis_representation().name)
        )
        with open(str(query_premis_rep_destination), "w") as f:
            f.write(profile_template.render(bag_path=self.bag_path))

        # Run SPARQL-anything transformation.
        sa = SparqlAnything()
        try:
            sip_graph = sa.construct(q=str(query_sip_destination), f="TTL")
            profile_descriptive_ie = sa.construct(
                q=str(query_descriptive_ie_destination), f="TTL"
            )
            profile_premis_ie = sa.construct(
                q=str(query_premis_ie_destination), f="TTL"
            )
            profile_premis_rep = sa.construct(
                q=str(query_premis_rep_destination), f="TTL"
            )

            data_graph = (
                sip_graph
                + profile_descriptive_ie
                + profile_premis_ie
                + profile_premis_rep
            )

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
        shacl_graph = Graph()
        shacl_graph.parse(str(self.shacl_sip()), format="turtle")
        shacl_graph.parse(str(self.shacl_profile()), format="turtle")
        conforms, results_graph, results_text = shacl_validate(
            data_graph=data_graph,
            shacl_graph=shacl_graph,
            meta_shacl=True,
            allow_warnings=True,
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
    def query_descriptive_ie() -> Path:
        return Path(
            "app",
            "resources",
            "1.1",
            "basic",
            "sparql",
            "descriptive_ie.sparql",
        )

    @staticmethod
    def query_premis_ie() -> Path:
        return Path(
            "app",
            "resources",
            "1.1",
            "basic",
            "sparql",
            "premis_ie.sparql",
        )

    @staticmethod
    def query_premis_representation() -> Path:
        return Path(
            "app",
            "resources",
            "1.1",
            "basic",
            "sparql",
            "premis_representation.sparql",
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


class MaterialArtworkProfile11(Profile):
    def profile_name() -> str:
        return "https://data.hetarchief.be/id/sip/1.1/material-artwork"

    @staticmethod
    def query_sip() -> Path:
        return Path(
            "app",
            "resources",
            "1.1",
            "material_artwork",
            "sparql",
            "sip.sparql",
        )

    @staticmethod
    def query_descriptive_ie() -> Path:
        return Path(
            "app",
            "resources",
            "1.1",
            "material_artwork",
            "sparql",
            "descriptive_ie.sparql",
        )

    @staticmethod
    def query_descriptive_representation() -> Path:
        return Path(
            "app",
            "resources",
            "1.1",
            "material_artwork",
            "sparql",
            "descriptive_representation.sparql",
        )

    @staticmethod
    def query_premis_ie() -> Path:
        return Path(
            "app",
            "resources",
            "1.1",
            "material_artwork",
            "sparql",
            "premis_ie.sparql",
        )

    @staticmethod
    def query_premis_representation() -> Path:
        return Path(
            "app",
            "resources",
            "1.1",
            "material_artwork",
            "sparql",
            "premis_representation.sparql",
        )

    @staticmethod
    def shacl_sip() -> Path:
        return Path(
            "app",
            "resources",
            "1.1",
            "material_artwork",
            "shacl",
            "sip.shacl.ttl",
        )

    @staticmethod
    def shacl_basic_profile() -> Path:
        return Path(
            "app",
            "resources",
            "1.1",
            "basic",
            "shacl",
            "basic.shacl.ttl",
        )

    @staticmethod
    def shacl_profile() -> Path:
        return Path(
            "app",
            "resources",
            "1.1",
            "material_artwork",
            "shacl",
            "material_artwork.shacl.ttl",
        )

    @staticmethod
    def premis_xsd() -> Path:
        return Path(
            "app",
            "resources",
            "1.1",
            "material_artwork",
            "xsd",
            "premis-v3-0.xsd",
        )

    @staticmethod
    def mets_xsd() -> Path:
        return Path(
            "app",
            "resources",
            "1.1",
            "material_artwork",
            "xsd",
            "mets.xsd",
        )

    @staticmethod
    def dc_schema_xsd() -> Path:
        return Path(
            "app",
            "resources",
            "1.1",
            "material_artwork",
            "xsd",
            "descriptive_material_artwork.xsd",
        )

    def _validate_premis(self) -> list[XMLNotValidError]:
        """Validate the PREMIS files.

        Material profile has multiple premis files, one on the package level and
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

    def _validate_descriptive(self) -> list[XMLNotValidError]:
        """Validate the dc+schema files.

        Material artwork profile has at least one file with the descriptive
        metadata on IE level. Every representation potentially has descriptive
        metadata as well.

        Returns:
            A list with errors detailing the parse/validation errors.
        """

        errors = []

        dc_schema_xsd = etree.XMLSchema(etree.parse(self.dc_schema_xsd()))

        # DC+SCHEMA on package level
        dcterms_package_path: Path = self.bag_path.joinpath(
            "data",
            "metadata",
            "descriptive",
            "dc+schema.xml",
        )
        try:
            dcterms_package = etree.parse(dcterms_package_path)
            dc_schema_xsd.assertValid(dcterms_package)
        except (etree.DocumentInvalid, etree.ParseError) as e:
            errors.append(XMLNotValidError(str(e.error_log)))

        # DC+SCHEMA on representation level
        for dcterms_representation_path in self.bag_path.glob(
            str(
                Path(
                    "data",
                    "representations",
                    "representation_*",
                    "metadata",
                    "descriptive",
                    "dc+schema.xml",
                )
            )
        ):
            try:
                dcterms_representation = etree.parse(dcterms_representation_path)
                dc_schema_xsd.assertValid(dcterms_representation)
            except (etree.DocumentInvalid, etree.ParseError) as e:
                errors.append(XMLNotValidError(str(e.error_log)))

        return errors

    def _validate_mets(self) -> list[XMLNotValidError]:
        """Validate the METS files.

        Basic profile has multiple METS files, one on the package level and one for
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

        Basic profile has:
            - Multiple METS files (package and one per representation level).
            - Multiple PREMIS files (package one per and representation level).
            - One or more descriptive metadata file (dc+schema on package and possible
              one per representation level).

        Returns:
            A list with errors detailing the parse/validation errors.
        """
        errors: list = self._validate_premis()
        errors.extend(self._validate_mets())
        errors.extend(self._validate_descriptive())

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

        # write SPARQL-anything query for the descriptive metadata on IE level.
        query_descriptive_ie_destination = self.bag_path.joinpath(
            self.query_descriptive_ie().name
        )
        profile_template = self.jinja_env.get_template(
            str(self.query_descriptive_ie().name)
        )
        with open(str(query_descriptive_ie_destination), "w") as f:
            f.write(profile_template.render(bag_path=self.bag_path))

        # write SPARQL-anything query for the descriptive metadata on representation level.
        query_descriptive_rep_destination = self.bag_path.joinpath(
            self.query_descriptive_representation().name
        )
        profile_template = self.jinja_env.get_template(
            str(self.query_descriptive_representation().name)
        )

        descriptive_representation_sparqls = []
        for path in self.bag_path.glob(
            str(
                Path(
                    "data",
                    "representations",
                    "representation_*",
                    "metadata",
                    "descriptive",
                    "dc+schema.xml",
                )
            )
        ):
            descriptive_representation_sparql: Path = (
                query_descriptive_rep_destination.with_name(
                    f"descriptive_{path.parts[-4]}.sparql"
                )
            )
            with open(
                descriptive_representation_sparql,
                "w",
            ) as f:
                f.write(profile_template.render(path=path))
            descriptive_representation_sparqls.append(descriptive_representation_sparql)

        # write SPARQL-anything query for the premis metadata on the IE level.
        query_premis_ie_destination = self.bag_path.joinpath(
            self.query_premis_ie().name
        )
        profile_template = self.jinja_env.get_template(str(self.query_premis_ie().name))
        with open(str(query_premis_ie_destination), "w") as f:
            f.write(profile_template.render(bag_path=self.bag_path))

        # write SPARQL-anything query for the premis metadata on the representation level.
        query_premis_rep_destination = self.bag_path.joinpath(
            self.query_premis_representation().name
        )
        profile_template = self.jinja_env.get_template(
            str(self.query_premis_representation().name)
        )

        premis_representation_sparqls = []
        for path in self.bag_path.glob(
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
            premis_representation_sparql: Path = query_premis_rep_destination.with_name(
                f"premis_{path.parts[-4]}.sparql"
            )
            with open(
                premis_representation_sparql,
                "w",
            ) as f:
                f.write(profile_template.render(path=path, rep_folder=path.parts[-4]))
            premis_representation_sparqls.append(premis_representation_sparql)

        # Run SPARQL-anything transformation.
        sa = SparqlAnything()
        try:
            sip_graph = sa.construct(q=str(query_sip_destination), f="TTL")
            # Descriptive on IE level.
            profile_descriptive = sa.construct(
                q=str(query_descriptive_ie_destination), f="TTL"
            )
            # Preservation on IE level.
            profile_premis_ie = sa.construct(
                q=str(query_premis_ie_destination), f="TTL"
            )

            data_graph = sip_graph + profile_descriptive + profile_premis_ie

            # Descriptive on representation level.
            for descriptive_representation_sparql in descriptive_representation_sparqls:

                profile_descriptive_rep = sa.construct(
                    q=str(descriptive_representation_sparql), f="TTL"
                )
                data_graph = data_graph + profile_descriptive_rep

            # Preservation on representation level.
            for premis_representation_sparql in premis_representation_sparqls:

                profile_premis_rep = sa.construct(
                    q=str(premis_representation_sparql), f="TTL"
                )
                data_graph = data_graph + profile_premis_rep

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
        # a premis:intellectualEntity node.
        if (
            None,
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
            URIRef("http://www.loc.gov/premis/rdf/v3/IntellectualEntity"),
        ) not in data_graph:
            raise GraphNotConformError(
                "Graph is perceived as empty as it does not contain an intellectual entity."
            )
        shacl_graph = Graph()
        shacl_graph.parse(str(self.shacl_sip()), format="turtle")
        shacl_graph.parse(str(self.shacl_basic_profile()), format="turtle")
        shacl_graph.parse(str(self.shacl_profile()), format="turtle")

        conforms, results_graph, results_text = shacl_validate(
            data_graph=data_graph,
            shacl_graph=shacl_graph,
            meta_shacl=True,
            allow_warnings=True,
        )

        if not conforms:
            raise GraphNotConformError(results_text)

        return True

class NewspaperProfile11(Profile):
    def profile_name() -> str:
        return "https://data.hetarchief.be/id/sip/1.1/newspaper"


    @staticmethod
    def query_sip() -> Path:
        return Path(
            "app",
            "resources",
            "1.1",
            "newspaper",
            "sparql",
            "sip.sparql",
        )

    @staticmethod
    def query_descriptive_ie() -> Path:
        return Path(
            "app",
            "resources",
            "1.1",
            "newspaper",
            "sparql",
            "descriptive_ie.sparql",
        )

    @staticmethod
    def query_descriptive_representation() -> Path:
        return Path(
            "app",
            "resources",
            "1.1",
            "newspaper",
            "sparql",
            "descriptive_representation.sparql",
        )

    @staticmethod
    def query_premis_ie() -> Path:
        return Path(
            "app",
            "resources",
            "1.1",
            "newspaper",
            "sparql",
            "premis_ie.sparql",
        )

    @staticmethod
    def query_premis_representation() -> Path:
        return Path(
            "app",
            "resources",
            "1.1",
            "newspaper",
            "sparql",
            "premis_representation.sparql",
        )

    @staticmethod
    def premis_xsd() -> Path:
        return Path(
            "app",
            "resources",
            "1.1",
            "newspaper",
            "xsd",
            "premis-v3-0.xsd",
        )

    @staticmethod
    def mets_xsd() -> Path:
        return Path(
            "app",
            "resources",
            "1.1",
            "newspaper",
            "xsd",
            "mets.xsd",
        )

    @staticmethod
    def mods_xsd() -> Path:
        return Path(
            "app",
            "resources",
            "1.1",
            "newspaper",
            "xsd",
            "mods-3-7.xsd",
        )

    @staticmethod
    def shacl_sip() -> Path:
        return Path(
            "app",
            "resources",
            "1.1",
            "newspaper",
            "shacl",
            "sip.shacl.ttl",
        )

    @staticmethod
    def shacl_basic_profile() -> Path:
        return Path(
            "app",
            "resources",
            "1.1",
            "basic",
            "shacl",
            "basic.shacl.ttl",
        )

    @staticmethod
    def shacl_profile() -> Path:
        return Path(
            "app",
            "resources",
            "1.1",
            "newpspaper",
            "shacl",
            "newspaper.shacl.ttl",
        )

    def _validate_premis(self) -> list[XMLNotValidError]:
        """Validate the PREMIS files.

        Newspaper profile has multiple premis files, one on the package level and
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


    def _validate_descriptive(self) -> list[XMLNotValidError]:
        """Validate the MODS or dc+schema files.

        Newspaper profile has at least one file with the descriptive
        metadata on IE level. Every representation potentially has descriptive
        metadata as well.

        Only MODS is implemented for now.

        Returns:
            A list with errors detailing the parse/validation errors.
        """

        errors = []

        mods_xsd = etree.XMLSchema(etree.parse(self.mods_xsd()))

        # DC+SCHEMA on package level
        dcterms_package_path: Path = self.bag_path.joinpath(
            "data",
            "metadata",
            "descriptive",
            "mods.xml",
        )
        try:
            dcterms_package = etree.parse(dcterms_package_path)
            mods_xsd.assertValid(dcterms_package)
        except (etree.DocumentInvalid, etree.ParseError) as e:
            errors.append(XMLNotValidError(str(e.error_log)))

        # MODS on representation level
        for dcterms_representation_path in self.bag_path.glob(
            str(
                Path(
                    "data",
                    "representations",
                    "representation_*",
                    "metadata",
                    "descriptive",
                    "mods.xml",
                )
            )
        ):
            try:
                dcterms_representation = etree.parse(dcterms_representation_path)
                mods_xsd.assertValid(dcterms_representation)
            except (etree.DocumentInvalid, etree.ParseError) as e:
                errors.append(XMLNotValidError(str(e.error_log)))

        return errors

    def _validate_mets(self) -> list[XMLNotValidError]:
        """Validate the METS files.

        Newspapr profile has multiple METS files, one on the package level and one for
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

        Basic profile has:
            - Multiple METS files (package and one per representation level).
            - Multiple PREMIS files (package one per and representation level).
            - One or more descriptive metadata file (dc+schema on package and possible
              one per representation level).

        Returns:
            A list with errors detailing the parse/validation errors.
        """
        errors: list = self._validate_premis()
        errors.extend(self._validate_mets())
        errors.extend(self._validate_descriptive())

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

        # write SPARQL-anything query for the descriptive metadata on IE level.
        query_descriptive_ie_destination = self.bag_path.joinpath(
            self.query_descriptive_ie().name
        )
        profile_template = self.jinja_env.get_template(
            str(self.query_descriptive_ie().name)
        )
        with open(str(query_descriptive_ie_destination), "w") as f:
            f.write(profile_template.render(bag_path=self.bag_path))

        # write SPARQL-anything query for the descriptive metadata on representation level.
        query_descriptive_rep_destination = self.bag_path.joinpath(
            self.query_descriptive_representation().name
        )
        profile_template = self.jinja_env.get_template(
            str(self.query_descriptive_representation().name)
        )

        descriptive_representation_sparqls = []
        for path in self.bag_path.glob(
            str(
                Path(
                    "data",
                    "representations",
                    "representation_*",
                    "metadata",
                    "descriptive",
                    "mods.xml",
                )
            )
        ):
            descriptive_representation_sparql: Path = (
                query_descriptive_rep_destination.with_name(
                    f"descriptive_{path.parts[-4]}.sparql"
                )
            )
            with open(
                descriptive_representation_sparql,
                "w",
            ) as f:
                f.write(profile_template.render(path=path))
            descriptive_representation_sparqls.append(descriptive_representation_sparql)

        # write SPARQL-anything query for the premis metadata on the IE level.
        query_premis_ie_destination = self.bag_path.joinpath(
            self.query_premis_ie().name
        )
        profile_template = self.jinja_env.get_template(str(self.query_premis_ie().name))
        with open(str(query_premis_ie_destination), "w") as f:
            f.write(profile_template.render(bag_path=self.bag_path))

        # write SPARQL-anything query for the premis metadata on the representation level.
        query_premis_rep_destination = self.bag_path.joinpath(
            self.query_premis_representation().name
        )
        profile_template = self.jinja_env.get_template(
            str(self.query_premis_representation().name)
        )

        premis_representation_sparqls = []
        for path in self.bag_path.glob(
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
            premis_representation_sparql: Path = query_premis_rep_destination.with_name(
                f"premis_{path.parts[-4]}.sparql"
            )
            with open(
                premis_representation_sparql,
                "w",
            ) as f:
                f.write(profile_template.render(path=path, rep_folder=path.parts[-4]))
            premis_representation_sparqls.append(premis_representation_sparql)

        # Run SPARQL-anything transformation.
        sa = SparqlAnything()
        try:
            sip_graph = sa.construct(q=str(query_sip_destination), f="TTL")
            # Descriptive on IE level.
            profile_descriptive = sa.construct(
                q=str(query_descriptive_ie_destination), f="TTL"
            )
            # Preservation on IE level.
            profile_premis_ie = sa.construct(
                q=str(query_premis_ie_destination), f="TTL"
            )

            data_graph = sip_graph + profile_descriptive + profile_premis_ie

            # Descriptive on representation level.
            for descriptive_representation_sparql in descriptive_representation_sparqls:

                profile_descriptive_rep = sa.construct(
                    q=str(descriptive_representation_sparql), f="TTL"
                )
                data_graph = data_graph + profile_descriptive_rep

            # Preservation on representation level.
            for premis_representation_sparql in premis_representation_sparqls:

                profile_premis_rep = sa.construct(
                    q=str(premis_representation_sparql), f="TTL"
                )
                data_graph = data_graph + profile_premis_rep

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
        # a premis:intellectualEntity node.
        if (
            None,
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
            URIRef("http://www.loc.gov/premis/rdf/v3/IntellectualEntity"),
        ) not in data_graph:
            raise GraphNotConformError(
                "Graph is perceived as empty as it does not contain an intellectual entity."
            )
        shacl_graph = Graph()
        shacl_graph.parse(str(self.shacl_sip()), format="turtle")
        shacl_graph.parse(str(self.shacl_basic_profile()), format="turtle")
        # shacl_graph.parse(str(self.shacl_profile()), format="turtle")

        conforms, results_graph, results_text = shacl_validate(
            data_graph=data_graph,
            shacl_graph=shacl_graph,
            meta_shacl=True,
            allow_warnings=True,
        )

        if not conforms:
            raise GraphNotConformError(results_text)

        return True


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
    elif profile_type == BasicProfile11.profile_name():
        return BasicProfile11(path)
    elif profile_type == MaterialArtworkProfile11.profile_name():
        return MaterialArtworkProfile11(path)
    elif profile_type == NewspaperProfile11.profile_name():
        return NewspaperProfile11(path)

    raise ValueError(f"Profile not known: {profile_type}.")
