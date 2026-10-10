# rftwin package — not yet in this repo

`run_all.py` at the repo root imports this package:

```python
from rftwin import RadioConfig, load_deepmimo, load_synthetic
from rftwin import kpi, site_selection, outage, radiomap, beam, mobility, viz
```

The following module source files have not been uploaded to this repo yet and are
missing from this directory:

- `rftwin/data.py` (`load_deepmimo`, `load_synthetic`, `RadioConfig`)
- `rftwin/kpi.py`
- `rftwin/site_selection.py`
- `rftwin/outage.py`
- `rftwin/radiomap.py`
- `rftwin/beam.py`
- `rftwin/mobility.py`
- `rftwin/viz.py`
- `rftwin/__init__.py`

`run_all.py` will not run until these are added. Add them with `git add rftwin/*.py`
once you have the source files.
