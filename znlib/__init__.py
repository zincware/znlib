"""The znlib package."""
import importlib.metadata

from znlib import nodes

__version__ = importlib.metadata.version("znlib")

__all__ = ["nodes"]
