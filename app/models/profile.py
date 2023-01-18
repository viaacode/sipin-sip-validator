from pathlib import Path


class Profile:
    def __init__(self, bag_path: Path):
        self.bag_path = bag_path


class BasicProfile(Profile):
    def handle(self):
        pass
