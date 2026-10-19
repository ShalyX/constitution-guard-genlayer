# ConstitutionGuard production plan

## Product boundary

ConstitutionGuard is a semantic compliance gate for DAO and protocol
governance execution. It does not create votes, custody treasury assets, or
claim that a proposal is economically wise. It answers one narrower question:
does the proposed action satisfy every declared constitutional clause using
the public evidence that was bound to the proposal?

The first release is intentionally receipt- and evidence-oriented. It fetches
the constitution sources, proposal evidence, and optional prior-resolution
references inside GenLayer's non-deterministic flow. Source content is treated
as untrusted evidence and is never allowed to rewrite contract rules.

## Critical user path

1. A constitution owner registers a versioned constitution, clause set, public
   source URLs, and active state.
2. A proposer submits a proposal with a bounded action summary, evidence URLs,
   optional prior-resolution references, an expiry, and a designated executor.
3. Anyone triggers evaluation. Validators independently fetch every declared
   source and classify every clause.
4. The contract stores the complete clause partition and only issues a permit
   for healthy sources, unanimous clause satisfaction, and high confidence.
5. The designated executor consumes the permit once. A downstream executor
   finalizes the protected effect only after the internal call is finalized.

## Hardening requirements

- Constitution updates increment a version and invalidate older proposals.
- Every clause ID must appear exactly once in each leader and validator result.
- Validator comparison binds the decision, clause partition, reason codes,
  confidence, source health, and source fingerprints.
- Source failures produce no permit, even if a model returns approval.
- Permit validation and consumption both require high confidence and a
  nonzero nonce issued by the approval path; low/medium-confidence approvals
  must fail closed even if their stored status is `approved`.
- Proposals expire before evaluation and permits expire before consumption.
- Executors are bound to an exact address and cannot be replaced by callers.
- A consumed permit cannot be replayed.
- UI clients must read finalized state instead of treating a submitted
  transaction as success.

## Release path

### Contract release

1. Run direct behavioral tests and GenVM lint.
2. Deploy `ConstitutionGuard` to StudioNet.
3. Deploy `GovernedExecutor` with the guard address.
4. Register a public constitution with stable, authoritative URLs.
5. Run live positive, rejected, unavailable-source, stale-version, wrong
   caller, expiry, and replay scenarios.
6. Publish the exact addresses, source manifests, test output, and finalized
   transaction links.

### Product release

The later project layer will provide wallet onboarding, constitution and clause
editing, proposal submission, evidence preview, consensus progress, public
proposal readback, and executor finalization. It must support refresh and
reconnect at every asynchronous step and show explicit pending, rejected,
invalidated, expired, consumed, and finalized states.

## Acceptance gates

- Direct and integration tests are green.
- The deployed contract rejects incomplete or conflicting clause partitions.
- A live approved proposal consumes exactly once.
- A changed constitution invalidates an otherwise approved proposal.
- Source failure and unavailable references cannot issue a permit.
- Low- and medium-confidence approvals with nonce `0` are neither valid nor
  consumable permits.
- The public readback shows the complete clause result and source fingerprints.
- The production app never displays a local-only approval.


