from dataclasses import dataclass
from pathlib import Path


@dataclass
class ConfigurationFile:

    path: str

    @property
    def instance(self):
        return Path(self.path).parts[2]

    @property
    def module(self):
        return Path(self.path).parts[3]

    @property
    def filename(self):
        return Path(self.path).name
