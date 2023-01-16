"""The znlib package"""
import importlib.metadata
import importlib.util

from znlib import utils

__version__ = importlib.metadata.version("znlib")

__all__ = ["utils"]

if importlib.util.find_spec("zntrack") is not None:
    from znlib import examples  # noqa: F401
    from znlib import scripts

    __all__ += ["examples", "scripts"]

if importlib.util.find_spec("ase") is not None:
    from znlib import atomistic  # noqa: F401

    __all__.append("atomistic")
