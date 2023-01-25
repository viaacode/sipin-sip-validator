from pathlib import Path

import bagit


class BagParseError(Exception):
    pass


class BagNotValidError(Exception):
    pass


class Bag:
    """Wrapper around the bagit library.

    Attributes:
        bag_path: The path of the bag.
    """

    def __init__(self, bag_path: Path):
        self.bag_path: Path = bag_path

    def parse_validate(self) -> bool:
        """Parse and validate the unzipped bag folder

        Returns:
            True if successful.

        Raises:
            - BagParseError: When the bag couldn't be parsed.
            - BagNotValidError: When the bag is not valid.
        """
        # Parse bag
        try:
            bag = bagit.Bag(str(self.bag_path))
        except bagit.BagError as e:
            raise BagParseError(str(e))

        # Validate bag
        try:
            bag.validate()
        except bagit.BagValidationError as e:
            raise BagNotValidError(str(e))

        return True
