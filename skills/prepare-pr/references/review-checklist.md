# Author preflight risk checklist

Use this as a set of **questions**, not mandatory issue quotas. Inspect only the risks relevant to the change, and prove or disprove each candidate through actual control flow, callers or tests.

## Change-set completeness

- Is the base/head comparison against the intended target branch and current commit?
- Does the independent inventory match the retrieved patch set? Are binary files, renames, deletions, generated output and submodules accounted for?
- Do new feature flags, configuration changes, migrations or external services create unreviewed interactions?

## Correctness and contracts

- What happens for empty, absent, malformed, duplicate, stale or out-of-order input?
- Do producer and consumer agree on types, formats, defaults and error semantics?
- Does the changed interface preserve callers, serialization, API compatibility and previously supported behavior?
- Is there a concrete regression test for the most important behavioral change?

## Security and trust boundaries

- Can untrusted input, path, URL, identity or environment variables cross a permission boundary?
- Are credentials, keys, PII and audit attribution handled safely in success **and** failure paths?
- Are authorization and scope checks enforced at the correct layer and again on state changes where needed?
- Can an error reveal secrets, skip safeguards or produce misleading success?

## Reliability and concurrency

- What if a process crashes, a network call times out, a retry repeats or the remote operation succeeds but the acknowledgment is lost?
- Can concurrent calls race, overwrite, duplicate or partially apply a mutation? Are operations idempotent where required?
- Are resource bounds, cleanup and backpressure appropriate? Is rollback/recovery safe?
- Can persisted or cached state become stale, especially across restart and deployment?

## Integration and operability

- Are configuration, compatibility, deployment sequencing and platform differences covered?
- Do logs and metrics represent the real actor and outcome without leaking sensitive data?
- Will older clients/Nodes/repositories fail safely rather than silently diverge?
- Are docs and tests aligned with actual tool permissions and runtime behavior?

## Tests and evidence

- Which checks were **personally executed**, which results were merely **observed in CI**, and which were unavailable?
- Were negative-path and regression tests added for actual bugs found during preflight?
- Do the PR description's base/head SHAs and test results still match the final reviewed commit?
- Are uncovered risks explicitly named, rather than described as passed?

### Finding quality

Report a suspected defect only with a credible trigger, affected path/line or function, impact and practical correction. Trace compensating safeguards first. An unverified concern can be marked as such; do not manufacture an issue or present a hypothesis as confirmed.
