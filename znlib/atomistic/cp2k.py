import contextlib
import pathlib
import shutil

import ase.calculators.cp2k
import yaml
from cp2k_input_tools.generator import CP2KInputGenerator
from zntrack import Node, dvc, meta, utils, zn

from znlib.atomistic.ase import AtomsList, ZnAtoms


class CP2KNode(Node):
    """CP2K Node

    This Node allows you to perform single point calculation using CP2K

    Parameters
    ----------
    atoms: AtomsList
        The ASE atoms objects to use. Typically, this is
        'znlib.atomistic.FileToASE() @ "atoms"' or some other Node output.
    input_file: str
        A yaml file as input for CP2k. A good way to generate is by using
        'fromcp2k --format yaml cp2k.inp > cp2k.yaml' from the cp2k-input-tools library.
    dependencies: list[str]
        Files such as the BASIS_SET_FILE or POTENTIAL_FILE should be passed as a
        dependency to check for changes in them.
    wfn_restart: str
        Typically, this would be 'CP2KNode().wfn_restart_file' from another Node.
        But it can also be another CP2K wavefunction restart file. Make sure to use
        'scf_guess: restart' to make use of it.

    References
    ----------
    https://www.cp2k.org/
    https://www.cp2k.org/howto:static_calculation
    https://databases.fysik.dtu.dk/ase/ase/calculators/cp2k.html
    https://github.com/cp2k/cp2k-input-tools

    """

    atoms: AtomsList = zn.deps()
    input_file: str = dvc.params()
    # e.g. "env OMP_NUM_THREADS=2 mpiexec -np 4 cp2k_shell.psmp"
    cp2k_shell: str = meta.Text("cp2k_shell.psmp")
    label: str = meta.Text("cp2k")

    outputs: AtomsList = ZnAtoms()

    cp2k_output_dir: pathlib.Path = dvc.outs(utils.nwd / "cp2k")

    dependencies = dvc.deps(None)
    wfn_restart = dvc.deps(None)

    stress_tensor: bool = True

    @staticmethod
    def _remove_unwanted_entries(data):
        """Remove entries from the 'input_file' that don't work with ASE"""
        with contextlib.suppress(KeyError):
            del data["force_eval"]["subsys"]["cell"]
        with contextlib.suppress(KeyError):
            del data["force_eval"]["subsys"]["coord"]
        with contextlib.suppress(KeyError):
            del data["global"]["project_name"]
        with contextlib.suppress(KeyError):
            del data["force_eval"]["print"]

        return data

    def get_calculator(self, script) -> ase.calculators.cp2k.CP2K:
        """Get an ASE CP2K calculator."""
        return ase.calculators.cp2k.CP2K(
            command=self.cp2k_shell,
            inp=script,
            basis_set=None,
            basis_set_file=None,
            max_scf=None,
            cutoff=None,
            force_eval_method=None,
            potential_file=None,
            poisson_solver=None,
            pseudo_potential=None,
            stress_tensor=self.stress_tensor,
            xc=None,
            print_level=None,
            label=self.label,
        )

    def _move_cp2k_outs(self):
        """The CP2K command is executed in the cwd.
        Output files will be moved to NWD afterward."""
        for file in pathlib.Path(".").glob(f"{self.label}*"):
            file.rename(self.cp2k_output_dir / file)

    @property
    def wfn_restart_file(self) -> pathlib.Path:
        # TODO if the file does not work return path to one of the backup files
        return self.cp2k_output_dir / f"{self.label}-RESTART.wfn"

    def run(self):
        # ! assert there are no files starting with cp2k_...
        # ! run cp2k
        # ! Do checkpoints?!?
        # ! move outputs
        # if self.cp2k_output_dir.exists():
        #     shutil.rmtree(self.cp2k_output_dir)
        self.cp2k_output_dir.mkdir()

        if self.wfn_restart is not None:
            # TODO maybe rename the file otherwise?
            assert pathlib.Path(self.wfn_restart).name == f"{self.label}-RESTART.wfn"
            shutil.copy(self.wfn_restart, ".")

        with open(self.input_file, "r") as file:
            cp2k_input_dict = yaml.safe_load(file)

        cp2k_input_dict = self._remove_unwanted_entries(cp2k_input_dict)

        cp2k_input_script = "\n".join(CP2KInputGenerator().line_iter(cp2k_input_dict))

        calc = self.get_calculator(cp2k_input_script)

        self.outputs = []
        for atom in self.atoms:
            assert isinstance(atom, ase.Atoms)
            atom = atom.copy()
            atom.calc = calc
            atom.get_potential_energy()
            self.outputs.append(atom)

        self._move_cp2k_outs()
