[![Coverage Status](https://coveralls.io/repos/github/zincware/znlib/badge.svg?branch=main)](https://coveralls.io/github/zincware/znlib?branch=main)
![PyTest](https://github.com/zincware/znlib/actions/workflows/pytest.yaml/badge.svg)
[![PyPI version](https://badge.fury.io/py/znlib.svg)](https://badge.fury.io/py/znlib)
[![ZnTrack](https://img.shields.io/badge/Powered%20by-ZnTrack-%23007CB0)](https://zntrack.readthedocs.io/en/latest/)

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
