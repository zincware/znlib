"""Collection of common fixtures
References
----------
https://docs.pytest.org/en/6.2.x/fixture.html#scope-sharing-fixtures-across-classes-modules-packages-or-session
"""
import os
import pathlib
import random
import shutil
import subprocess

import ase.io
import pytest


@pytest.fixture
def proj_path(tmp_path, request) -> pathlib.Path:
    """temporary directory for testing DVC calls
    Parameters
    ----------
    tmp_path
    request: https://docs.pytest.org/en/6.2.x/reference.html#std-fixture-request
    Returns
    -------
    path to temporary directory
    """
    shutil.copy(request.module.__file__, tmp_path)
    os.chdir(tmp_path)
    subprocess.check_call(["git", "init"])
    subprocess.check_call(["dvc", "init"])

    subprocess.check_call(["git", "add", "."])
    subprocess.check_call(["git", "commit", "-m", "initial commit"])

    return tmp_path


@pytest.fixture
def tetraeder_test_traj(tmp_path_factory) -> str:
    """Generate n atoms objects of random shifts of a CH4 tetraeder."""
    # different tetraeder

    tetraeder = ase.Atoms(
        "CH4",
        positions=[(1, 1, 1), (0, 0, 0), (0, 2, 2), (2, 2, 0), (2, 0, 2)],
        cell=(2, 2, 2),
    )

    random.seed(42)

    atoms = [tetraeder.copy() for _ in range(20)]
    [x.rattle(stdev=0.5, seed=random.randint(1, int(1e6))) for x in atoms]

    temporary_path = tmp_path_factory.getbasetemp()
    file = temporary_path / "tetraeder.extxyz"
    ase.io.write(file, atoms)
    return file.resolve().as_posix()
