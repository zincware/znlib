"""Test MC Pi."""

import pytest

import znlib


def test_MonteCarloPiEstimator(proj_path) -> None:
    """Test MonteCarloPiEstimator."""
    node = znlib.nodes.MonteCarloPiEstimator(n_points=1000, seed=1234)
    node.write_graph()
    node.run_and_save()

    assert node.load().estimate == pytest.approx(3.1415, abs=0.1)


def test_ComputeCircleArea(proj_path) -> None:
    """Test ComputeCircleArea based on Monte Carlo Pi."""
    mcpi = znlib.nodes.MonteCarloPiEstimator(n_points=1000, seed=1234)
    mcpi.write_graph()
    mcpi.run_and_save()

    area = znlib.nodes.ComputeCircleArea(pi_estimator=mcpi, radius=1.0)
    area.write_graph()
    area.run_and_save()

    assert area.load().area == pytest.approx(3.1415, abs=0.1)
