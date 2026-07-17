# Engineering Intelligence — companion code

Runnable companions to the book _Engineering Intelligence_. Two projects live here:

## `notebooks/`

Seven analysis notebooks that reproduce the worked examples in the book, so a
reader can type numbers from their own organization into the same computations
and get a defensible answer. Each notebook is a plain `.py` file with `# %%`
cell markers — open it in Jupyter, VS Code, PyCharm, or run it as a script.

| Notebook | Book reference |
| --- | --- |
| `01-queueing-cost.py` | Ch 2, worked example on queueing delay |
| `02-cost-distribution.py` | Ch 2, right-skewed cost distributions |
| `03-context-switch-cost.py` | Ch 4, quantifying context-switch cost |
| `04-causal-did-cace.py` | Ch 6, did the AI reviewer actually help? |
| `05-power-and-mde.py` | Ch 6, statistical power and MDE |
| `06-blast-radius-scoring.py` | Ch 9, scoring a shared-library change |
| `07-flow-bundle-interpretation.py` | Ch 11, reading the flow bundle |

Each notebook is self-contained and takes seconds to run.

## `synth/`

`engintel_synth` is a Python module that emits realistic-shaped engineering
telemetry — pull-request events, review comments, CI runs, deployments,
incidents, teams, and Engineering-Change groupings — without requiring access
to any real organisation's data. It exists so the notebooks (and any
downstream reconstruction, metric, or experiment work) have a substrate to
operate on.

Usage:

```
pip install -e companion/synth
python -m engintel_synth --days 30 --teams 40 --seed 42 --out data/
```

The generator is deterministic given a seed; two runs with the same
parameters produce byte-identical output.

## Install

```
pip install -r companion/requirements.txt
pip install -e companion/synth
```

Only `numpy`, `scipy`, and `matplotlib` are needed for the notebooks;
the synth generator additionally uses standard-library `random` and `json`.
