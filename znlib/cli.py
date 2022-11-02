"""Command Line Interface"""
import dataclasses
import importlib.metadata
from importlib.util import find_spec

from colorama import Fore, Style


@dataclasses.dataclass
class ZnModules:
    """Collect information about installed zincware packages"""

    name: str

    installed: bool = dataclasses.field(init=False)

    def __post_init__(self):
        self.installed = find_spec(self.name) is not None
        self.print_status()

    def print_status(self):
        """Print the installed version if available"""
        if self.installed:
            version = importlib.metadata.version(self.name)
            print(
                f" {Fore.GREEN} ✓ {Fore.LIGHTCYAN_EX} {self.name} {Style.RESET_ALL} \t"
                f" ({version})"
            )
        else:
            print(f" {Fore.RED} ✗ {Fore.LIGHTCYAN_EX} {self.name} {Style.RESET_ALL}")


def znlib_status():
    """All zincware packages that should be listed"""
    print(f"Available {Fore.LIGHTBLUE_EX}zincware{Style.RESET_ALL} packages:")

    packages = sorted(
        [
            "znlib",
            "zntrack",
            "mdsuite",
            "znjson",
            "zninit",
            "dot4dict",
            "znipy",
            "supercharge",
            "znvis",
            "symdet",
            "aaargs",
        ]
    )
    for package in packages:
        ZnModules(package)
