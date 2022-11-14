import subprocess

import pytest

from znlib import examples


@pytest.mark.parametrize("ExampleNode", (examples.InputToOutput, examples.InputToMetric))
def test_InputToOutput(proj_path, ExampleNode):
    node = ExampleNode(inputs=25)
    node.write_graph()
    node.run_and_save()

    assert node.load().inputs == 25
    assert node.load().outputs == 25


def test_AddInputs(proj_path):
    node = examples.AddInputs(a=5, b=10)
    node.write_graph()
    node.run_and_save()

    assert node.load().a == 5
    assert node.load().b == 10
    assert node.load().result == 15


def test_InputToOutputMeta(proj_path):
    node = examples.InputToOutputMeta(inputs=25, author="Fabian")
    node.write_graph()
    node.run_and_save()

    assert node.load().inputs == 25
    assert node.load().outputs == 25
    assert node.load().author == "Fabian"


def test_MonteCarloPiEstimator(proj_path):
    node = examples.MonteCarloPiEstimator(n_points=1000, seed=1234)
    node.write_graph()
    node.run_and_save()

    assert node.load().estimate == pytest.approx(3.1415, abs=0.1)


def test_ComputeCircleArea(proj_path):
    mcpi = examples.MonteCarloPiEstimator(n_points=1000, seed=1234)
    mcpi.write_graph()
    mcpi.run_and_save()

    area = examples.ComputeCircleArea(pi_estimator=mcpi, radius=1.0)
    area.write_graph()
    area.run_and_save()

    assert area.load().area == pytest.approx(3.1415, abs=0.1)


def test_ComputeMeanStd(proj_path):
    nodes = []
    for idx in range(7):
        node = examples.RandomNumber(seed=idx, name=f"node_{idx}")
        node.write_graph()
        nodes.append(node)

    mean = examples.ComputeMeanStd(inputs=nodes)
    mean.write_graph()

    subprocess.check_call(["dvc", "repro"])

    mean = mean.load()

    assert mean.mean == pytest.approx(0.5, abs=0.1)


def test_TimeToMetric():
    node = examples.TimeToMetric()
    node.run()
    assert node.time > 0.0
