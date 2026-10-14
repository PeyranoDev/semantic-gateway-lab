# AoristoTech integration

Run from the repository root, with the pinned private source and a fresh disposable
PostgreSQL database. See [the protocol](../../docs/aoristo-protocol.md) for setup,
cost accounting and limits.

```bash
python -m unittest discover -s tests -v
python -m integrations.aoristo.run --source ../AoristoTech \
  --database-url postgresql://lab:lab@127.0.0.1:55432/sglab_aoristo \
  --out results/local-aoristo
```

`model.py` defines synthetic actors/actions and legitimate seeds. `adapter.py`
preserves the original request pipeline and SQL persistence. `oracle.py` specifies
the adopted domain policy independently. `generator.py` implements generic
mutations without regression knowledge. `experiment.py` accounts for every call
and shrinks witnesses. `regressions.py` checks known cases and positive controls.
`run.py` validates replays and writes compressed data, paired summaries and provenance.

No private backend implementation is copied into this public repository.
