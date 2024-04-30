from pathlib import Path

from lxml import etree
from rdflib import Graph

from app.models.profiles.exceptions import XMLNotValidError, GraphParseError
from app.models.profiles.profile import Profile, sa


class BasicProfile11(Profile):
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

    def _validate_descriptive(self) -> list[XMLNotValidError]:
        """Validate the dcterms file.

        Basic profile has one file with the descriptive metadata.

        Returns:
            A parse/validation error in a list if applicable.
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
            return [XMLNotValidError(str(e.error_log))]

        return []

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

    def _construct_shacl_graph(self) -> Graph:
        shacl_graph = Graph()
        shacl_graph.parse(str(self.shacl_sip()), format="turtle")
        shacl_graph.parse(str(self.shacl_profile()), format="turtle")
        return shacl_graph


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

    def _construct_shacl_graph(self) -> Graph:
        shacl_graph = Graph()
        shacl_graph.parse(str(self.shacl_sip()), format="turtle")
        shacl_graph.parse(str(self.shacl_basic_profile()), format="turtle")
        shacl_graph.parse(str(self.shacl_profile()), format="turtle")
        return shacl_graph


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
    def query_file_page_representation() -> Path:
        return Path(
            "app",
            "resources",
            "1.1",
            "newspaper",
            "sparql",
            "file_page.sparql",
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
    def shacl_profile() -> Path:
        return Path(
            "app",
            "resources",
            "1.1",
            "newspaper",
            "shacl",
            "newspaper.shacl.ttl",
        )

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

        # MODS on package level
        mods_package_path: Path = self.bag_path.joinpath(
            "data",
            "metadata",
            "descriptive",
            "mods.xml",
        )
        try:
            mods_package = etree.parse(mods_package_path)
            mods_xsd.assertValid(mods_package)
        except (etree.DocumentInvalid, etree.ParseError) as e:
            errors.append(XMLNotValidError(str(e.error_log)))

        # MODS on representation level
        for mods_representation_path in self.bag_path.glob(
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
                mods_representation = etree.parse(mods_representation_path)
                mods_xsd.assertValid(mods_representation)
            except (etree.DocumentInvalid, etree.ParseError) as e:
                errors.append(XMLNotValidError(str(e.error_log)))

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

        # write SPARQL-anything query for the file page information.
        profile_template = self.jinja_env.get_template(
            str(self.query_file_page_representation().name)
        )

        file_page_sparqls = []
        for path in self.bag_path.glob(
            str(
                Path(
                    "data",
                    "representations",
                    "representation_*",
                )
            )
        ):
            premis_file_page_sparql: Path = query_premis_rep_destination.with_name(
                f"file_page_{path.parts[-1]}.sparql"
            )
            with open(
                premis_file_page_sparql,
                "w",
            ) as f:
                f.write(profile_template.render(path=path))
            file_page_sparqls.append(premis_file_page_sparql)

        # Run SPARQL-anything transformation.
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

            # File page information.
            for file_page_sparql in file_page_sparqls:

                profile_file_page = sa.construct(q=str(file_page_sparql), f="TTL")
                data_graph = data_graph + profile_file_page

        except Exception as e:
            raise GraphParseError(f"Error when parsing graph: {str(e)}")

        return data_graph

    def _construct_shacl_graph(self) -> Graph:
        shacl_graph = Graph()
        shacl_graph.parse(str(self.shacl_sip()), format="turtle")
        shacl_graph.parse(str(self.shacl_profile()), format="turtle")
        return shacl_graph
