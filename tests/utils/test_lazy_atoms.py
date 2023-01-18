"""Test Lazy Atoms."""
import ase
from zntrack import Node

from znlib.utils.lazy_atoms import ASEAtomsFromDB, Atoms


class AtomsData(Node):
    """Node with Atoms ZnTrackOption."""

    atoms = Atoms()

    def run(self):
        """Generate Atoms data."""
        self.atoms = [
            ase.Atoms("CO", positions=[(0, 0, 0), (0, 0, idx)]) for idx in range(10)
        ]


def test_ASEAtomsFromDB(ase_db):
    """Test ASEAtomsFromDB."""
    db = ASEAtomsFromDB(ase_db.as_posix(), threshold=10)
    assert len(db) == 10
    data = db[[1, 3, 5]].tolist()
    for idx, atoms in zip([1, 3, 5], data):
        # atoms positions identify the id
        assert atoms.get_positions()[1][2] == idx


def test_AtomsData(proj_path):
    """Test Node with Atoms."""
    data = AtomsData()
    data.run_and_save()

    data = AtomsData.load()

    assert len(data.atoms) == 10
    assert data.atoms[1].get_positions()[1][2] == 1
    assert data.atoms[[1, 3, 5]].tolist()[1].get_positions()[1][2] == 3
    assert data.atoms[[1, 3, 5]].tolist()[2].get_positions()[1][2] == 5
