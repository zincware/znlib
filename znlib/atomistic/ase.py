"""Atomic Simulation Environment interface for znlib / ZnTrack """
import contextlib
import logging
import pathlib
import typing

import ase.calculators.singlepoint
import ase.db
import ase.geometry.analysis
import ase.io
import numpy as np
import pandas as pd
import tqdm
from zntrack import Node, dvc, utils, zn
from zntrack.core import ZnTrackOption

import znlib.utils

log = logging.getLogger(__name__)

AtomsList = typing.List[ase.Atoms]


class ASEAtomsFromDB:
    def __init__(self, database: str, threshold: int = 100):
        """Default __init__
        Parameters
        ----------
        database: file
            The database to read from
        threshold: int
            Minimum number of atoms to read at once to print tqdm loading bars
        """
        self._database = pathlib.Path(database)
        self._threshold = threshold
        self._len = None

    def __getitem__(self, item) -> typing.Union[ase.Atoms, AtomsList]:
        """Get atoms
        Parameters
        ----------
        item: int | list | slice
            The identifier of the requested atoms to return
        Returns
        -------
        Atoms | list[Atoms]
        """

        indices = znlib.utils.lazy.item_to_list(item, len(self))
        atoms = []

        with ase.db.connect(self._database) as database:
            for key in tqdm.tqdm(
                indices,
                disable=len(indices) < self._threshold,
                ncols=120,
                desc=f"Loading atoms from {self._database}",
            ):
                atoms.append(database[key + 1].toatoms())
        return atoms[0] if isinstance(item, int) else atoms

    def __len__(self):
        """Get the len based on the db. This value is cached because
        the db is not expected to change during the lifetime of this class
        """
        if self._len is None:
            with ase.db.connect(self._database) as db:
                self._len = len(db)
        return self._len

    def __repr__(self):
        db_short = "/".join(self._database.parts[-3:])
        return f"{self.__class__.__name__}(db='{db_short}')"


class ZnAtoms(ZnTrackOption):
    """Store list[ase.Atoms] in an ASE database."""

    dvc_option = "outs"
    zn_type = utils.ZnTypes.RESULTS

    def get_filename(self, instance) -> pathlib.Path:
        """Overwrite filename to csv"""
        return pathlib.Path("nodes", instance.node_name, f"{self.name}.db")

    def save(self, instance):
        """Save value with ase.db.connect"""
        atoms: AtomsList = getattr(instance, self.name)
        file = self.get_filename(instance)

        with ase.db.connect(file, append=False) as db:
            for atom in tqdm.tqdm(atoms, desc=f"Writing atoms to {file}"):
                _atom = atom.copy()

                if atom.calc is not None:
                    # Save properties to SinglePointCalculator
                    properties = {}
                    with contextlib.suppress(
                        ase.calculators.singlepoint.PropertyNotImplementedError
                    ):
                        properties["energy"] = atom.get_potential_energy()
                    with contextlib.suppress(
                        ase.calculators.singlepoint.PropertyNotImplementedError
                    ):
                        properties["forces"] = atom.get_forces()
                    with contextlib.suppress(
                        ase.calculators.singlepoint.PropertyNotImplementedError
                    ):
                        properties["stress"] = atom.get_stress()

                    if properties:
                        calc = ase.calculators.singlepoint.SinglePointCalculator(
                            atoms=_atom, **properties
                        )
                        _atom.calc = calc
                db.write(_atom, group=instance.node_name)

    def get_data_from_files(self, instance) -> znlib.utils.lazy.LazyList:
        """Load value with ase.db.connect"""
        return znlib.utils.lazy.LazyList(
            ASEAtomsFromDB(database=self.get_filename(instance).resolve().as_posix())
        )


class FileToASE(Node):
    """Read an ASE compatible file and make it available as list of atoms objects

    The atoms object is a LazyAtomsSequence
    """

    file: typing.Union[str, pathlib.Path] = dvc.deps()
    frames_to_read: int = zn.params(None)

    atoms: AtomsList = ZnAtoms()

    def post_init(self):
        if not self.is_loaded:
            self.file = pathlib.Path(self.file)
            dvc_file = pathlib.Path(self.file.name + ".dvc")
            if not dvc_file.exists():
                log.warning(
                    "The File you are adding as a dependency does not seem to be tracked"
                    f" by DVC. Please run 'dvc add {self.file}' to avoid tracking the"
                    " file directly with GIT."
                )

    def run(self):
        self.atoms = []
        for config, atom in enumerate(
            tqdm.tqdm(ase.io.iread(self.file), desc="Reading File")
        ):
            if self.frames_to_read is not None:
                if config >= self.frames_to_read:
                    break
            self.atoms.append(atom)


class RadialDistributionFunction(Node):
    """Compute a RadialDistributionFunction from a list of ase.Atoms

    Attributes
    ----------
    rmax: float
            Maximum distance of RDF.
    nbins: int
            Number of bins to divide RDF.

    elements: str/int/list/tuple
            Make partial RDFs. If elements is *None*, a full RDF is calculated. If
            elements is an *integer* or a *list/tuple of integers*, only those atoms will
            contribute to the RDF (like a mask). If elements is a *string* or a
            *list/tuple of strings*, only Atoms of those elements will contribute.
    """

    rmax: float = zn.params()
    nbins: int = zn.params()
    elements: str = zn.params(None)

    plot: pd.DataFrame = zn.plots(x="x", x_label=r"distance r", y_label=r"RDF g(r)")

    data: AtomsList = zn.deps()

    def run(self):
        analysis = ase.geometry.analysis.Analysis(list(self.data))
        data = analysis.get_rdf(rmax=self.rmax, nbins=self.nbins, elements=self.elements)

        self.plot = pd.DataFrame(
            {"x": np.linspace(0, self.rmax, self.nbins), "y": np.mean(data, axis=0)}
        )
        self.plot.set_index("x")
