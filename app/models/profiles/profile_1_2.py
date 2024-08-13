from pathlib import Path
from lxml import etree
from rdflib import Graph

from app.models.profiles.profile import sa
from app.models.profiles.exceptions import XMLNotValidError, GraphParseError
from app.models.profiles.profile_1_1 import (
    BasicProfile11,
    NewspaperProfile11,
    MaterialArtworkProfile11,
)


class BasicProfile12(BasicProfile11):
    def profile_name() -> str:
        return "https://data.hetarchief.be/id/sip/1.2/basic"

    @staticmethod
    def query_sip() -> Path:
        return Path(
            "app",
            "resources",
            "1.2",
            "basic",
            "sparql",
            "sip.sparql",
        )

    @staticmethod
    def query_descriptive_ie() -> Path:
        return Path(
            "app",
            "resources",
            "1.2",
            "basic",
            "sparql",
            "descriptive_ie.sparql",
        )

    @staticmethod
    def query_premis_ie() -> Path:
        return Path(
            "app",
            "resources",
            "1.2",
            "basic",
            "sparql",
            "premis_ie.sparql",
        )

    @staticmethod
    def query_premis_representation() -> Path:
        return Path(
            "app",
            "resources",
            "1.2",
            "basic",
            "sparql",
            "premis_representation.sparql",
        )

    @staticmethod
    def shacl_sip() -> Path:
        return Path(
            "app",
            "resources",
            "1.2",
            "basic",
            "shacl",
            "sip.shacl.ttl",
        )

    @staticmethod
    def shacl_profile() -> Path:
        return Path(
            "app",
            "resources",
            "1.2",
            "basic",
            "shacl",
            "basic.shacl.ttl",
        )

    @staticmethod
    def shacl_profile_schema() -> Path:
        return Path(
            "app",
            "resources",
            "1.2",
            "basic",
            "shacl",
            "basic_schema.shacl.ttl",
        )

    @staticmethod
    def premis_xsd() -> Path:
        return Path(
            "app",
            "resources",
            "1.2",
            "basic",
            "xsd",
            "premis-v3-0.xsd",
        )

    @staticmethod
    def mets_xsd() -> Path:
        return Path(
            "app",
            "resources",
            "1.2",
            "basic",
            "xsd",
            "mets.xsd",
        )

    @staticmethod
    def dcterms_xsd() -> Path:
        raise NotImplementedError

    @staticmethod
    def dc_schema_xsd() -> Path:
        return Path(
            "app",
            "resources",
            "1.2",
            "basic",
            "xsd",
            "descriptive_basic.xsd",
        )

    def _validate_descriptive(self) -> list[XMLNotValidError]:
        """Validate the dc+schema file.

        Basic profile has one file with the descriptive metadata.

        Returns:
            A parse/validation error in a list if applicable.
        """
        dcterms_xsd = etree.XMLSchema(etree.parse(self.dc_schema_xsd()))

        dcterms_package_path: Path = self.bag_path.joinpath(
            "data",
            "metadata",
            "descriptive",
            "dc+schema.xml",
        )

        # DCTERMS on package level
        try:
            dcterms_package = etree.parse(dcterms_package_path)
            dcterms_xsd.assertValid(dcterms_package)
        except (etree.DocumentInvalid, etree.ParseError) as e:
            return [XMLNotValidError(str(e.error_log))]

        return []

    def _construct_shacl_graph(self) -> Graph:
        shacl_graph = Graph()
        shacl_graph.parse(str(self.shacl_sip()), format="turtle")
        shacl_graph.parse(str(self.shacl_profile_schema()), format="turtle")
        shacl_graph.parse(str(self.shacl_profile()), format="turtle")
        return shacl_graph


class MaterialArtworkProfile12(MaterialArtworkProfile11):
    def profile_name() -> str:
        return "https://data.hetarchief.be/id/sip/1.2/material-artwork"

    @staticmethod
    def query_sip() -> Path:
        return Path(
            "app",
            "resources",
            "1.2",
            "material_artwork",
            "sparql",
            "sip.sparql",
        )

    @staticmethod
    def query_descriptive_ie() -> Path:
        return Path(
            "app",
            "resources",
            "1.2",
            "material_artwork",
            "sparql",
            "descriptive_ie.sparql",
        )

    @staticmethod
    def query_descriptive_representation() -> Path:
        return Path(
            "app",
            "resources",
            "1.2",
            "material_artwork",
            "sparql",
            "descriptive_representation.sparql",
        )

    @staticmethod
    def query_premis_ie() -> Path:
        return Path(
            "app",
            "resources",
            "1.2",
            "material_artwork",
            "sparql",
            "premis_ie.sparql",
        )

    @staticmethod
    def query_premis_representation() -> Path:
        return Path(
            "app",
            "resources",
            "1.2",
            "material_artwork",
            "sparql",
            "premis_representation.sparql",
        )

    @staticmethod
    def shacl_sip() -> Path:
        return Path(
            "app",
            "resources",
            "1.2",
            "material_artwork",
            "shacl",
            "sip.shacl.ttl",
        )

    @staticmethod
    def shacl_basic_profile() -> Path:
        return Path(
            "app",
            "resources",
            "1.2",
            "basic",
            "shacl",
            "basic.shacl.ttl",
        )

    @staticmethod
    def shacl_profile() -> Path:
        return Path(
            "app",
            "resources",
            "1.2",
            "material_artwork",
            "shacl",
            "material_artwork.shacl.ttl",
        )

    @staticmethod
    def premis_xsd() -> Path:
        return Path(
            "app",
            "resources",
            "1.2",
            "material_artwork",
            "xsd",
            "premis-v3-0.xsd",
        )

    @staticmethod
    def mets_xsd() -> Path:
        return Path(
            "app",
            "resources",
            "1.2",
            "material_artwork",
            "xsd",
            "mets.xsd",
        )

    @staticmethod
    def dc_schema_xsd() -> Path:
        return Path(
            "app",
            "resources",
            "1.2",
            "material_artwork",
            "xsd",
            "descriptive_material_artwork.xsd",
        )


class BibliographicProfile12(NewspaperProfile11):
    def profile_name() -> str:
        return "https://data.hetarchief.be/id/sip/1.2/bibliographic"

    @staticmethod
    def query_sip() -> Path:
        return Path(
            "app",
            "resources",
            "1.2",
            "bibliographic",
            "sparql",
            "sip.sparql",
        )

    @staticmethod
    def query_descriptive_ie() -> Path:
        return Path(
            "app",
            "resources",
            "1.2",
            "bibliographic",
            "sparql",
            "descriptive_ie.sparql",
        )

    @staticmethod
    def query_descriptive_representation() -> Path:
        return Path(
            "app",
            "resources",
            "1.2",
            "bibliographic",
            "sparql",
            "descriptive_representation.sparql",
        )

    @staticmethod
    def query_premis_ie() -> Path:
        return Path(
            "app",
            "resources",
            "1.2",
            "bibliographic",
            "sparql",
            "premis_ie.sparql",
        )

    @staticmethod
    def query_premis_representation() -> Path:
        return Path(
            "app",
            "resources",
            "1.2",
            "bibliographic",
            "sparql",
            "premis_representation.sparql",
        )

    @staticmethod
    def query_file_page_representation() -> Path:
        return Path(
            "app",
            "resources",
            "1.2",
            "bibliographic",
            "sparql",
            "file_page.sparql",
        )

    @staticmethod
    def premis_xsd() -> Path:
        return Path(
            "app",
            "resources",
            "1.2",
            "bibliographic",
            "xsd",
            "premis-v3-0.xsd",
        )

    @staticmethod
    def mets_xsd() -> Path:
        return Path(
            "app",
            "resources",
            "1.2",
            "bibliographic",
            "xsd",
            "mets.xsd",
        )

    @staticmethod
    def mods_xsd() -> Path:
        return Path(
            "app",
            "resources",
            "1.2",
            "bibliographic",
            "xsd",
            "mods-3-7.xsd",
        )

    @staticmethod
    def shacl_sip() -> Path:
        return Path(
            "app",
            "resources",
            "1.2",
            "bibliographic",
            "shacl",
            "sip.shacl.ttl",
        )

    @staticmethod
    def shacl_profile() -> Path:
        return Path(
            "app",
            "resources",
            "1.2",
            "bibliographic",
            "shacl",
            "bibliographic.shacl.ttl",
        )

    @staticmethod
    def shacl_premis() -> Path:
        return Path(
            "app",
            "resources",
            "1.2",
            "bibliographic",
            "shacl",
            "premis.shacl.ttl",
        )
