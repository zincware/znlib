"""CP2K Single Point Calculator."""
import functools
import pathlib
import subprocess
from unittest.mock import patch

import ase.calculators.cp2k
import ase.io
import tqdm
import yaml
from cp2k_input_tools.generator import CP2KInputGenerator
from zntrack import Node, dvc, meta, utils, zn


class CP2KSinglePoint(Node):
    """
    Node for running CP2K Single point calculations.

    Args:
        cp2k_shell: name of the CP2K-shell used.
        cp2k_params: inputfile for CP2K.
        atoms: ase atoms object.
        atoms_file: if atoms are provided through
            a file and not a node, the path should be
            declared here.
        output_file: path to the output file
        cp2k_directory: path to cp2k output directory


    Returns:
        None
    """
    cp2k_shell: str = meta.Text("cp2k_shell.ssmp")
    cp2k_params = dvc.params("cp2k.yaml")

    atoms = zn.deps(None)
    atoms_file = dvc.deps(None)

    output_file = dvc.outs(utils.nwd / "atoms.extxyz")
    cp2k_directory = dvc.outs(utils.nwd / "cp2k")

    def run(self):
        """ZnTrack run method."""
        if self.atoms_file != None:
            self.atoms = list(ase.io.iread(self.atoms_file))

        self.cp2k_directory.mkdir(exist_ok=True)
        with open(self.cp2k_params, "r") as file:
            cp2k_input_dict = yaml.safe_load(file)

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

        with patch(
            "ase.calculators.cp2k.Popen",
            wraps=functools.partial(subprocess.Popen, cwd=self.cp2k_directory),
        ):
            calculator = ase.calculators.cp2k.CP2K(
                command=self.cp2k_shell,
                inp=cp2k_input_script,
                basis_set=None,
                basis_set_file=None,
                max_scf=None,
                cutoff=None,
                force_eval_method=None,
                potential_file=None,
                poisson_solver=None,
                pseudo_potential=None,
                stress_tensor=True,
                xc=None,
                print_level=None,
                label="cp2k",
            )

            for atom in tqdm.tqdm(self.atoms):
                atom.calc = calculator
                atom.get_potential_energy()
                ase.io.write(self.output_file.as_posix(), atom, append=True)
    @functools.cached_property
    def results(self):
        """Get the Atoms list."""
        # TODO this should probably be a Atoms object.
        return list(ase.io.iread(self.output_file))
