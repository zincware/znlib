"""Example Nodes that are categorized as general nodes."""
import datetime
import random
import time
import typing

import numpy as np
from zntrack import Node, meta, zn


class InputToOutput(Node):
    """Save the inputs 'zn.params' to the outputs attribute 'zn.outs'"""

    inputs = zn.params()
    outputs = zn.outs()

    def run(self):
        self.outputs = self.inputs


class InputToMetric(InputToOutput):
    """Save the inputs 'zn.params' to the outputs attribute 'zn.metrics'"""

    outputs = zn.metrics()


class InputToOutputMeta(InputToOutput):
    """Add author via 'meta.Text' which will not affect the graph

    The 'zntrack.meta.Text' offers a  way to add information to a Node,
    which is not used as a parameter or a dependency.
    """

    author: str = meta.Text()


class AddInputs(Node):
    """Compute the 'zn.params' a + b = result 'zn.metrics'"""

    a = zn.params()
    b = zn.params()
    result = zn.metrics()

    def run(self):
        self.result = self.a + self.b


class RandomNumber(Node):
    """Generate a random number"""

    seed: int = zn.params()
    number: float = zn.outs()

    def run(self):
        random.seed(self.seed)
        self.number = random.random()


class HasNumber(typing.Protocol):
    """Type Hint for any class implementing a 'number' attribute"""

    number: float


class ComputeMeanStd(Node):
    """Compute the mean and std over the given numbers"""

    inputs: typing.List[HasNumber] = zn.deps()
    mean: float = zn.metrics()
    std: float = zn.metrics()

    def run(self):
        numbers = [x.number for x in self.inputs]
        self.mean = np.mean(numbers)
        self.std = np.std(numbers)


class TimeToMetric(Node):
    """Use Datetime to save the current time

    This can e.g. be useful to measure parallel execution tasks.

    Parameters
    ----------
    time: float, Time to wait before storing the current time.
    strftime: text: Format in which to store the time. Must be convertible to float.

    """

    time = zn.metrics()
    sleep: float = zn.params(0.0)

    strftime: str = meta.Text("%H%M%S.%f")

    def run(self):
        time.sleep(self.sleep)
        self.time = float(datetime.datetime.now().strftime(self.strftime))
