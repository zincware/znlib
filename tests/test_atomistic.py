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


def test_LammpsSimulator(proj_path):
    simulator = znlib.atomistic.LammpsSimulator(
        extras={"temperature": 1234, "npt": {"steps": 100}}
    )
    simulator.system.units = "lj"

    template = simulator.get_template()

    # modify the template by extra arguments.
    with open(template, "a") as file:
        file.write("velocity       all create {{ temperature }} 132465")
        file.write("run             {{ npt.steps }}")

    simulator.write_graph()
    simulator = simulator.load()
    simulator.render_template()
    assert simulator.system.units == "lj"
    assert simulator.extras == {"temperature": 1234, "npt": {"steps": 100}}

    checks = 0  # count all assertions and make sure all where called

    with open(simulator.input_file) as file:
        for line in file:
            if "units" in line:
                assert simulator.system.units in line
                checks += 1
            if "boundary" in line:
                assert simulator.system.boundary in line
                checks += 1
            if "atom_style" in line:
                assert simulator.system.atom_style in line
                checks += 1
            if "velocity" in line:
                assert str(simulator.extras["temperature"]) in line
                checks += 1
            if "run" in line:
                assert str(simulator.extras["npt"]["steps"]) in line
                checks += 1

    assert checks == 5
