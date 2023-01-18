"""Collection of common fixtures.

References
----------
https://docs.pytest.org/en/6.2.x/fixture.html#scope-sharing-fixtures-across-classes-modules-packages-or-session
"""
import os
import pathlib
import shutil

import ase.db
import dvc.cli
import git
import pytest


@pytest.fixture
def proj_path(tmp_path, request) -> pathlib.Path:
    """Temporary directory for testing DVC calls.

    Parameters
    ----------
    tmp_path:
        temporary directory
    request:
        https://docs.pytest.org/en/6.2.x/reference.html#std-fixture-request

    Returns
    -------
    path to temporary directory
    """
    shutil.copy(request.module.__file__, tmp_path)
    os.chdir(tmp_path)

    git.Repo.init()
    dvc.cli.main(["init"])

    return tmp_path


@pytest.fixture
def ase_db(tmp_path, request) -> pathlib.Path:
    """Generate ASE database."""
    db_file = tmp_path / "atoms.db"

    with ase.db.connect(db_file) as db:
        for idx in range(10):
            atoms = ase.Atoms("CO", positions=[(0, 0, 0), (0, 0, idx)])
            db.write(atoms, group="data")

    return db_file
