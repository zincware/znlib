import collections.abc
import logging
import pathlib
import typing

import ase.db
import ase.io
import tqdm
from zntrack import Node, dvc, utils, zn
from zntrack.core import ZnTrackOption

log = logging.getLogger(__name__)

ATOMS_LST = typing.List[ase.Atoms]


class LazyAtomsSequence(collections.abc.Sequence):
    """Sequence that loads atoms objects from ase Database only when accessed

    This sequence does not support modifications but only reading values from it.
    """

    def __init__(self, db: str, threshold: int = 100):
        """Default __init__

        Parameters
        ----------
        db: file
            The database to read from
        threshold: int
            Minimum number of atoms to read at once to print tqdm loading bars
        """
        self._db = db
        self._threshold = threshold
        self.__dict__["atoms"]: typing.Dict[int, ase.Atoms] = {}
        self._len = None

    def _update_state_from_db(self, indices: list):
        """Load requested atoms into memory

        If the atoms are not present in __dict__ they will be read from db

        Parameters
        ----------
        indices: list
            The indices of the atoms. Indices are 0based and will be converted to 1 based
            when reading from the ase db.
        """
        indices = [x for x in indices if x not in self.__dict__["atoms"]]

        with ase.db.connect(self._db) as db:
            for key in tqdm.tqdm(
                indices,
                disable=len(indices) < self._threshold,
                ncols=120,
                desc=f"Loading atoms from {self._db}",
            ):
                self.__dict__["atoms"][key] = db[key + 1].toatoms()

    def __iter__(self):
        """Enable iterating over the sequence. This will load all data at once"""
        self._update_state_from_db(list(range(len(self))))
        for idx in range(len(self)):
            yield self[idx]

    def __getitem__(self, item) -> typing.Union[ase.Atoms, ATOMS_LST]:
        """Get atoms

        Parameters
        ----------
        item: int | list | slice
            The identifier of the requested atoms to return

        Returns
        -------
        Atoms | list[Atoms]

        """
        if isinstance(item, int):
            # The most simple case
            try:
                return self.__dict__["atoms"][item]
            except KeyError:
                self._update_state_from_db([item])
                return self.__dict__["atoms"][item]
        # everything with lists
        if isinstance(item, slice):
            item = list(range(len(self)))[item]

        try:
            return [self.__dict__["atoms"][x] for x in item]
        except KeyError:
            self._update_state_from_db(item)
            return [self.__dict__["atoms"][x] for x in item]

    def __len__(self):
        """Get the len based on the db. This value is cached because
        the db is not expected to change during the lifetime of this class
        """
        if self._len is None:
            with ase.db.connect(self._db) as db:
                self._len = len(db)
        return self._len

    def __repr__(self):
        return f"{self.__class__.__name__}(db={self._db})"

    def tolist(self) -> ATOMS_LST:
        """Convert sequence to a list of atoms objects"""
        return [x for x in self]


class ZnAtoms(ZnTrackOption):
    """Store list[ase.Atoms] in an ASE database."""

    dvc_option = "outs"
    zn_type = utils.ZnTypes.RESULTS

    def get_filename(self, instance) -> pathlib.Path:
        """Overwrite filename to csv"""
        return pathlib.Path("nodes", instance.node_name, f"{self.name}.db")

    def save(self, instance):
        """Save value with ase.db.connect"""
        atoms: ATOMS_LST = self.__get__(instance, self.owner)
        file = self.get_filename(instance)
        # file.parent.mkdir(exist_ok=True, parents=True)
        with ase.db.connect(file, append=False) as db:
            for atom in tqdm.tqdm(atoms, desc=f"Writing atoms to {file}"):
                db.write(atom, group=instance.node_name)

    def get_data_from_files(self, instance) -> LazyAtomsSequence:
        """Load value with ase.db.connect"""
        return LazyAtomsSequence(db=self.get_filename(instance).resolve().as_posix())


class FileToASE(Node):
    """Read a ASE compatible file and make it available as list of atoms objects

    The atoms object is a LazyAtomsSequence
    """

    file: typing.Union[str, pathlib.Path] = dvc.deps()
    frames_to_read: int = zn.params(None)

    atoms: ATOMS_LST = ZnAtoms()

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
