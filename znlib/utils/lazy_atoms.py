"""Lazy ASE Atoms loading."""
import collections.abc
import contextlib
import pathlib
import typing

import ase.calculators.singlepoint
import ase.db
import tqdm
import znslice
import zntrack.core

ATOMS_LST = typing.List[ase.Atoms]


class ASEAtomsFromDB(collections.abc.Sequence):
    """ASE Atoms from ASE DB loading."""

    def __init__(self, database: str, threshold: int = 100):
        """Construct class with a default __init__.

        Parameters
        ----------
        database: file
            The database to read from
        threshold: int
            Minimum number of atoms to read at once to print tqdm loading bars.
        """
        self._database = pathlib.Path(database)
        self._threshold = threshold
        self._len = None

    @znslice.znslice(lazy=True, advanced_slicing=True)
    def __getitem__(
        self, item: typing.Union[int, list]
    ) -> typing.Union[ase.Atoms, znslice.LazySequence]:
        """Get atoms.

        Parameters
        ----------
        item: int | list | slice
            The identifier of the requested atoms to return
        Returns
        -------
        Atoms | list[Atoms].
        """
        atoms = []
        single_item = isinstance(item, int)
        if single_item:
            item = [item]

        with ase.db.connect(self._database) as database:
            for key in tqdm.tqdm(
                item,
                disable=len(item) < self._threshold,
                ncols=120,
                desc=f"Loading atoms from {self._database}",
            ):
                atoms.append(database[key + 1].toatoms())
        return atoms[0] if single_item else atoms

    def __len__(self):
        """Get the len based on the db.

        This value is cached because the db is not expected to
        change during the lifetime of this class.
        """
        if self._len is None:
            with ase.db.connect(self._database) as db:
                self._len = len(db)
        return self._len

    def __repr__(self):
        """Repr."""
        db_short = "/".join(self._database.parts[-3:])
        return f"{self.__class__.__name__}(db='{db_short}')"


class Atoms(zntrack.core.ZnTrackOption):
    """Store list[ase.Atoms] in an ASE database."""

    dvc_option = "outs"
    zn_type = zntrack.utils.ZnTypes.RESULTS

    def get_filename(self, instance) -> pathlib.Path:
        """Overwrite filename to csv."""
        return pathlib.Path("nodes", instance.node_name, f"{self.name}.db")

    def save(self, instance):
        """Save value with ase.db.connect."""
        atoms: ATOMS_LST = getattr(instance, self.name)
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

    def get_data_from_files(self, instance) -> ASEAtomsFromDB:
        """Load value with ase.db.connect."""
        return ASEAtomsFromDB(database=self.get_filename(instance).resolve().as_posix())
