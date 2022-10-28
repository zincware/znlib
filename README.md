# znlib
This package provides you with a CLI to list your installed zincware libraries.

When installing via `pip install znlib[zntrack]` your output should look something like:

```
>>> znlib
Available zincware packages:
  ✓  znlib       (0.1.0)
  ✓  zntrack     (0.4.3)
  ✗  mdsuite 
  ✓  znjson      (0.2.1)
  ✓  zninit      (0.1.1)
  ✓  dot4dict    (0.1.1)
  ✗  znipy 
  ✗  supercharge 
  ✗  znvis 
  ✗  symdet 
```

Furthermore, `znlib` provides you with some example [ZnTrack](https://github.com/zincware/ZnTrack) Nodes.

```python
from znlib.examples import MonteCarloPiEstimator

mcpi = MonteCarloPiEstimator(n_points=1000).write_graph(run=True)
print(mcpi.load().estimate)
>>> 3.128
```

The idea of the `znlib` package is to provide a collection of [ZnTrack](https://github.com/zincware/ZnTrack) Nodes from all different fields of research.
Every contribution is very welcome.
For new Nodes:
1. Fork this repository.
2. Create a file under the directory `znlib/examples`
3. Make a Pull request.

