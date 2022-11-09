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

CWD = pathlib.Path(__file__).parent


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


@pytest.fixture()
def atoms_si8() -> ase.Atoms:
    return ase.Atoms(
        "Si8",
        positions=[
            (0.000000000, 0.000000000, 0.000000000),
            (0.000000000, 2.715348700, 2.715348700),
            (2.715348700, 2.715348700, 0.000000000),
            (2.715348700, 0.000000000, 2.715348700),
            (4.073023100, 1.357674400, 4.073023100),
            (1.357674400, 1.357674400, 1.357674400),
            (1.357674400, 4.073023100, 4.073023100),
            (4.073023100, 4.073023100, 1.357674400),
        ],
        cell=(5.430697500, 5.430697500, 5.430697500),
    )


@pytest.fixture()
def cp2k_si8_input() -> dict:
    return {
        "global": {
            "project_name": "Si_bulk8",
            "run_type": "energy_force",
            "print_level": "LOW",
        },
        "force_eval": {
            "subsys": {
                "kind": {
                    "Si": {
                        "element": "Si",
                        "basis_set": "DZVP-GTH-PADE",
                        "potential": "GTH-PADE-q4",
                    }
                },
            },
            "DFT": {
                "QS": {"eps_default": "1e-10"},
                "mgrid": {"ngrids": 4, "cutoff": 300.0, "rel_cutoff": 60.0},
                "XC": {"xc_functional": {"_": "PADE"}},
                "SCF": {
                    "diagonalization": {"_": True, "algorithm": "standard"},
                    "mixing": {
                        "_": True,
                        "method": "broyden_mixing",
                        "alpha": 0.4,
                        "nbuffer": 8,
                    },
                    "scf_guess": "atomic",
                    "eps_scf": "1e-07",
                    "max_scf": 5,
                },
                "basis_set_file_name": "BASIS_SET",
                "potential_file_name": "GTH_POTENTIALS",
            },
            "print": {"forces": {"_": True}},
            "method": "quickstep",
        },
    }


@pytest.fixture()
def BASIS_SET() -> pathlib.Path:
    return CWD / "static" / "BASIS_SET"


@pytest.fixture()
def GTH_POTENTIALS() -> pathlib.Path:
    return CWD / "static" / "GTH_POTENTIALS"
