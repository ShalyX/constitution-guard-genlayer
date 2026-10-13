# ConstitutionGuard

ConstitutionGuard is a reusable GenLayer Intelligent Contract for governance
proposals that need more than a signature and a yes/no vote. A protocol or DAO
owner publishes a versioned constitution with explicit clauses. A proposer binds
an action to that constitution, supplies public evidence and optional prior
resolutions, and names the executor that may consume an approval permit.

GenLayer validators fetch the declared public sources inside the
non-deterministic flow and independently classify every clause as satisfied,
violated, or unclear. The contract stores the complete disjoint clause result,
source fingerprints, confidence band, and rationale. Only a high-confidence
approval with healthy sources issues a one-use permit. Constitution updates,
deactivation, expiry, wrong callers, and replay invalidate the execution path.

This first slice is contract-focused. It includes the reusable guard, a
finality-gated `GovernedExecutor` example, direct behavioral tests, a production
plan, and deployment notes. It does not pretend to replace a DAO's voting
mechanism; it supplies an auditable semantic compliance gate before an already
authorized proposal reaches a protected executor.

## Local verification

```powershell
python -m pytest tests/direct -q
```

The tests cover complete clause partitions, public-source retrieval, source
failure, stale constitution versions, expiry, executor authorization, permit
consumption, and replay.
