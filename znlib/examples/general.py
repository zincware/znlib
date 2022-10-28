"""Example Nodes that are categorized as general nodes."""
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
