# Next investigation after the AoristoTech case study

The v0.2 synthetic sequence study and v0.3 AoristoTech HTTP/PostgreSQL integration
are complete. See paper/sequence-results.md and paper/aoristo-results.md.

1. Review the adopted store/unit policies independently and fix the reproduced
   natural discrepancies on a separate application branch. Run the same regressions
   against the corrected counterpart before drawing mitigation conclusions.
2. Freeze a fresh-seed replication protocol before tuning the engines. Random
   exploration finds scope bugs more often; seeded mutation finds repeated
   cancellation more often. Test a hybrid explicitly rather than asserting a winner.
3. Separate full-budget state exploration from targeted failure stopping. Vary
   corpus capacity/retention and isolate workflow seeding from mutation.
4. Validate the real Alembic schema and independent transactions. Add concurrent
   invitation/QR consumption and partial-failure tests; the serial savepoint study
   does not establish race safety or production durability.
5. Add independently authored policies/defect families and a public reproducible
   domain. AoristoTech is another implementation by the same author and remains private.
6. Expand the document benchmark to generation-bound approvals and revocation.
7. Add versioned MCP transport, then a separately configured agent evaluation
   measuring legitimate tasks, adversarial tasks, runtime effects and call/token costs.

The current evidence contains no MCP transport, LLM agent, OPA process or production
deployment validation. The owner ablation is implemented in v0.2 but unmeasured;
department/task delegation ablations and broader novelty review remain pending.
