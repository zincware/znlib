"""Lammps Node"""
import dataclasses
import importlib.resources
import pathlib
import shutil
import subprocess

import jinja2
from zntrack import Node, dvc, meta, utils, zn

from znlib import data


@dataclasses.dataclass
class LammpsSystem:
    """Group Lammps parameters in dataclasses"""

    units: str = "metal"
    atom_style: str = "charge"
    boundary: str = "p p p"


class LammpsSimulator(Node):
    """A Lammps Node

    References
    ----------
    https://docs.lammps.org/

    Attributes
    ----------
    lammps_binary: str, default = "lmp"
        The name / path to the lammps binary

    template: str, default = "lammps.jinja2"
        The name of the jinja2 template file. Use get_template() as a starting point.

    system: LammpsSystem,
        a default Dataclass used in most lammps simulations
    extras: dict
        A dictionary of additional template variables that are by default not part
        of the 'lammps.jinja2' template shipped with znlib.
    """

    lammps_binary = meta.Text("lmp")

    template: str = dvc.deps("lammps.jinja2")

    output: pathlib.Path = dvc.outs(utils.nwd / ".")

    system: LammpsSystem = zn.params(LammpsSystem())
    extras: dict = zn.params({})

    def post_init(self):
        self.input_file = self.output / "input.lmp"
        self.log_file = self.output / "lammps.log"

    @staticmethod
    def get_template(filename: str = "lammps.jinja2") -> str:
        """Load a jinja2 template for lammps that ships with znlib

        Parameters
        ----------
        filename: str, default = "lammps.jinja2"
            The jinja2 template to be adapted for the use with LammpsSimulator
        """
        with importlib.resources.path(data, "lammps.jinja2") as file:
            shutil.copy(file, filename)
        return filename

    def render_template(self):
        """Write the lammps input file"""
        with open(self.template, "r", encoding="utf-8") as file:
            template = jinja2.Template(file.read())

        input_script = template.render(
            system=self.system, log_file=self.log_file, **self.extras
        )
        self.input_file.write_text(input_script)

    def run(self):
        """Run the lammps simulations"""
        self.render_template()
        subprocess.check_call([self.lammps_binary, "-in", self.input_file], shell=True)
