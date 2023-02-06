"""CP2K interface without ASE calculator.

This interface is less restrictive than CP2K Single Point.
"""
import pathlib
import subprocess

import ase.io
import yaml
from cp2k_input_tools.generator import CP2KInputGenerator
from zntrack import Node, dvc, meta, utils, zn


class CP2KYaml(Node):
    """Node for running CP2K Single point calculations."""

    cp2k_bin: str = meta.Text("cp2k.psmp")
    cp2k_params = dvc.params("cp2k.yaml")

    cp2k_directory: pathlib.Path = dvc.outs(utils.nwd / "cp2k")

    atoms_file = dvc.deps()  # TODO allow both, atoms file and atoms object
    index: int = zn.params(-1)

    def run(self):
        """ZnTrack run method."""
        self.cp2k_directory.mkdir(exist_ok=True)
        with open(self.cp2k_params, "r") as file:
            cp2k_input_dict = yaml.safe_load(file)

        atoms = list(ase.io.iread(self.atoms_file))
        atoms = atoms[self.index]
        # TODO assert that they do not exist
        cp2k_input_dict["force_eval"]["subsys"]["topology"] = {
            "COORD_FILE_FORMAT": "XYZ",
            "COORD_FILE_NAME": "atoms.xyz",
        }
        cp2k_input_dict["force_eval"]["subsys"]["cell"] = {
            "A": list(atoms.cell[0]),
            "B": list(atoms.cell[1]),
            "C": list(atoms.cell[2]),
        }

        cp2k_input_dict["force_eval"]["DFT"]["XC"]["vdw_potential"]["pair_potential"][
            "parameter_file_name"
        ] = (
            pathlib.Path(
                cp2k_input_dict["force_eval"]["DFT"]["XC"]["vdw_potential"][
                    "pair_potential"
                ]["parameter_file_name"]
            )
            .resolve()
            .as_posix()
        )
        cp2k_input_dict["force_eval"]["DFT"]["basis_set_file_name"] = (
            pathlib.Path(cp2k_input_dict["force_eval"]["DFT"]["basis_set_file_name"])
            .resolve()
            .as_posix()
        )
        cp2k_input_dict["force_eval"]["DFT"]["potential_file_name"] = (
            pathlib.Path(cp2k_input_dict["force_eval"]["DFT"]["potential_file_name"])
            .resolve()
            .as_posix()
        )

        cp2k_input_script = "\n".join(CP2KInputGenerator().line_iter(cp2k_input_dict))
        with self.operating_directory(move_on=subprocess.CalledProcessError):
            ase.io.write(self.cp2k_directory / "atoms.xyz", atoms)
            input_file = self.cp2k_directory / "input.cp2k"
            input_file.write_text(cp2k_input_script)

            subprocess.run(
                [self.cp2k_bin, "-in", self.cp2k_directory / "input.cp2k"],
                cwd=self.cp2k_directory,
                check=True,
            )
