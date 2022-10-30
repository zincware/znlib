import subprocess

from znlib.examples import ComputeMeanStd, RandomNumber


def converge_random_numbers(number_initial_nodes=2, tolerance=0.1) -> ComputeMeanStd:
    """Iteratively build a graph of Nodes that generate a Random Number and converge
    to 'abs(mean - 0.5) < tolerance'.
    """
    nodes = []
    for idx in range(number_initial_nodes):
        node = RandomNumber(seed=idx, name=f"RandomNumber_{idx}")
        node.write_graph()
        nodes.append(node)

    mean = ComputeMeanStd(inputs=nodes)
    mean.write_graph()

    subprocess.check_call(["dvc", "repro"])

    while True:
        mean = mean.load()
        print(f"Found {mean.mean} for n = {len(mean.inputs)}")
        if abs(mean.mean - 0.5) < tolerance:
            break

        seed = len(nodes) + 1

        node = RandomNumber(seed=seed, name=f"RandomNumber_{seed}")
        node.write_graph()
        nodes.append(node)

        mean = ComputeMeanStd(inputs=nodes)
        mean.write_graph()

        subprocess.check_call(["dvc", "repro"])

    print(
        f"Converged with n = {len(nodes)} random number draws to mean = {mean.mean}, std"
        f" = {mean.std}."
    )

    return mean
