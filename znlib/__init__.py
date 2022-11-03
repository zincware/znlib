"""The znlib package"""
import importlib.metadata
import importlib.util

__version__ = importlib.metadata.version("znlib")

__all__ = []

if importlib.util.find_spec("zntrack") is not None:
    from znlib import examples  # noqa: F401

    __all__.append("examples")

if importlib.util.find_spec("ase") is not None:
    from znlib import atomistic  # noqa: F401

    __all__.append("ase")

if importlib.util.find_spec("tensorflow") is not None:
    from znlib import tensorflow  # noqa: F401

    __all__.append("tensorflow")
