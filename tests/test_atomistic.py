import pathlib
import shutil
import subprocess

import ase

import znlib


def test_AddData(proj_path, tetraeder_test_traj):
    traj_file = pathlib.Path(tetraeder_test_traj)
    shutil.copy(traj_file, ".")

    subprocess.check_call(["dvc", "add", traj_file.name])
    data = znlib.atomistic.FileToASE(file=traj_file.name)
    data.run_and_save()

    loaded_data = znlib.atomistic.FileToASE.load()

    assert isinstance(loaded_data.atoms, znlib.atomistic.ase.LazyAtomsSequence)
    assert isinstance(loaded_data.atoms[0], ase.Atoms)
    assert loaded_data.atoms.__dict__["atoms"] == {0: loaded_data.atoms[0]}
    assert isinstance(loaded_data.atoms[[0, 1]], list)
    assert isinstance(loaded_data.atoms[:], list)
    assert isinstance(loaded_data.atoms.tolist(), list)
