from znlib import scripts


def test_converge_random_numbers(proj_path):
    mean = scripts.converge_random_numbers(number_initial_nodes=1, tolerance=0.05)

    assert abs(mean.mean - 0.5) < 0.1
    assert len(mean.inputs) > 1  # should be 8 with the given seed / params
