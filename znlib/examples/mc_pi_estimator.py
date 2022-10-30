"""Monte Carlo Method to Estimate Pi"""

import matplotlib.pyplot as plt
import numpy as np
from zntrack import Node, zn


def plot_sampling(ax, coordinates, n_points, estimate):
    """Plot a quarter of a circle with the sampled points"""
    circle = plt.Circle((0, 0), 1, fill=False, linewidth=3, edgecolor="k", zorder=10)

    ax.set_xlim(-0.0, 1.0)
    ax.set_ylim(-0.0, 1.0)
    ax.spines.left.set_position("zero")
    ax.spines.right.set_color("none")
    ax.spines.bottom.set_position("zero")
    ax.spines.top.set_color("none")
    ax.xaxis.set_ticks_position("bottom")
    ax.yaxis.set_ticks_position("left")
    ax.plot(coordinates[:, 0], coordinates[:, 1], ".")
    inner_points = np.array(list(filter(lambda x: np.linalg.norm(x) <= 1, coordinates)))
    ax.plot(inner_points[:, 0], inner_points[:, 1], "r.")
    ax.add_patch(circle)
    ax.set_title(rf"N: {n_points} ; $\pi$ = {estimate}")
    ax.set_aspect("equal")


class MonteCarloPiEstimator(Node):
    """Estimate pi by Monte Carlo Sampling"""

    n_points: int = zn.params()
    seed: int = zn.params(1234)

    coordinates: np.ndarray = zn.outs()
    estimate: float = zn.metrics()

    def run(self):
        """Compute pi using MC"""
        np.random.seed(self.seed)
        self.coordinates = np.random.random(size=(self.n_points, 2))
        radial_values = np.linalg.norm(self.coordinates, axis=1)
        n_circle_points = len(list(filter(lambda x: x <= 1, radial_values)))
        self.estimate = 4 * n_circle_points / self.n_points

    def plot(self, ax):
        """Create a plot of the sampled coordinates"""
        plot_sampling(
            ax,
            coordinates=self.coordinates,
            n_points=self.n_points,
            estimate=self.estimate,
        )


class ComputeCircleArea(Node):
    """Compute the area of a circle using the mc estimated pi"""

    pi_estimator: MonteCarloPiEstimator = zn.deps()
    radius: float = zn.params()

    area: float = zn.metrics()

    def run(self):
        self.area = self.pi_estimator.estimate * self.radius**2
