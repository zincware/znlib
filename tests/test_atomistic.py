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


def test_RadialDistributionFunction(proj_path, tetraeder_test_traj):
    traj_file = pathlib.Path(tetraeder_test_traj)
    shutil.copy(traj_file, ".")

    data = znlib.atomistic.FileToASE(file=traj_file.name)
    data.write_graph(run=True)

    rdf_h = znlib.atomistic.ase.RadialDistributionFunction(
        data=data @ "atoms", rmax=2.0, nbins=10, elements="H", name="rdf_H"
    )
    rdf_c = znlib.atomistic.ase.RadialDistributionFunction(
        data=data @ "atoms", rmax=2.0, nbins=10, elements="C", name="rdf_C"
    )
    rdf_ch = znlib.atomistic.ase.RadialDistributionFunction(
        data=data @ "atoms", rmax=2.0, nbins=10, elements=["C", "H"], name="rdf_CH"
    )

    rdf_h.write_graph()
    rdf_c.write_graph()
    rdf_ch.write_graph()

    rdf_h = znlib.atomistic.ase.RadialDistributionFunction.load(name="rdf_H")
    rdf_h.run_and_save()

    rdf_c = znlib.atomistic.ase.RadialDistributionFunction.load(name="rdf_C")
    rdf_c.run_and_save()

    rdf_ch = znlib.atomistic.ase.RadialDistributionFunction.load(name="rdf_CH")
    rdf_ch.run_and_save()

    assert len(rdf_h.plot) == 10
    assert len(rdf_c.plot) == 10
    assert len(rdf_ch.plot) == 10

    assert any(rdf_h.plot["y"] != rdf_c.plot["y"])
    assert any(rdf_h.plot["y"] != rdf_ch.plot["y"])
    assert any(rdf_c.plot["y"] != rdf_ch.plot["y"])

    assert sum(rdf_h.plot["y"]) > 0.0
    # assert sum(rdf_c.plot["y"]) > 0.0 # for the given tetraeder this is actually 0
    assert sum(rdf_ch.plot["y"]) > 0.0
