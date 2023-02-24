"""CP2K interface without ASE calculator.

This interface is less restrictive than CP2K Single Point.
"""
import pathlib
import shutil
import subprocess

import ase.io
import cp2k_output_tools
import pandas as pd
import yaml
from ase.calculators.singlepoint import SinglePointCalculator
from cp2k_input_tools.generator import CP2KInputGenerator
from zntrack import Node, dvc, meta, utils, zn


class CP2KYaml(Node):
    """Node for running CP2K Single point calculations."""

    cp2k_bin: str = meta.Text("cp2k.psmp")
    cp2k_params = dvc.params("cp2k.yaml")
    wfn_restart: str = dvc.deps(None)

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
        with self.operating_directory():
            ase.io.write(self.cp2k_directory / "atoms.xyz", atoms)
            input_file = self.cp2k_directory / "input.cp2k"
            input_file.write_text(cp2k_input_script)

            if self.wfn_restart is not None:
                shutil.copy(self.wfn_restart, self.cp2k_directory / "cp2k-RESTART.wfn")
            with subprocess.Popen(
                f"{self.cp2k_bin} -in input.cp2k",
                cwd=self.cp2k_directory,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            ) as proc:
                with open(self.cp2k_directory / "cp2k.log", "w") as file:
                    for line in proc.stdout:
                        file.write(line.decode("utf-8"))
                        print(line.decode("utf-8"), end="")
            if proc.returncode not in [0, None]:
                raise RuntimeError(f"CP2K failed with return code {proc.returncode}:")

    @property
    def atoms(self):
        """Return the atoms object."""
        data = {}
        with open(self.cp2k_directory / "cp2k.log", "r") as file:
            for match in cp2k_output_tools.parse_iter(file.read()):
                data.update(match)

        forces_df = pd.DataFrame(data["forces"]["atomic"]["per_atom"])
        forces = forces_df[["x", "y", "z"]].values

        atoms = ase.io.read(self.cp2k_directory / "atoms.xyz")
        atoms.calc = SinglePointCalculator(
            atoms=atoms, energy=data["energies"]["total force_eval"], forces=forces
        )

        return atoms
