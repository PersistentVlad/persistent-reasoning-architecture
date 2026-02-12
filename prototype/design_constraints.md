# Design Constraints

This document enumerates the **non-negotiable design constraints** enforced by the prototype.

These constraints are not implementation choices.
They are **architectural requirements**.

Relaxing any of them collapses persistent reasoning into familiar failure modes.

---

## Constraint 1: Singular Write Authority

There must exist **exactly one** architectural location where persistent structures can be mutated.

- Inference code must not write.
- Retrieval systems must not write.
- Learning pipelines must not write.
- Human interfaces must not write.

All mutation passes through a **write barrier**.

This is not an access-control concern.
It is an identity-preservation requirement.

---

## Constraint 2: Non-Queryability of Persistent Structures

Persistent structures must not be:
- queried,
- evaluated,
- solved,
- satisfied,
- optimized.

They may only be:
- navigated,
- compared structurally,
- versioned.

If a structure can answer questions, it has become executable.
Executable structures cannot persist without collapse.

---

## Constraint 3: Append-Only Persistence

Persistent identity must be preserved through **lineage**, not state mutation.

Therefore:
- no in-place updates,
- no overwrites,
- no deletions without lineage.

Revision creates a new version.
Old versions remain part of identity history.

---

## Constraint 4: Proposal–Commit Separation

Inference may:
- explore,
- suggest,
- propose.

Inference must never:
- commit,
- finalize,
- decide survival.

Commitment is a separate, deliberate act.

This separation prevents:
- implicit learning,
- accidental overwriting,
- optimization-driven collapse.

---

## Constraint 5: No Implicit Learning

The prototype forbids:
- gradient updates,
- reinforcement signals,
- continual learning,
- self-training loops.

Persistence is achieved only through **explicit revision**.

Learning changes capability.
Persistence preserves identity.

These must remain orthogonal.

---

## Constraint 6: No Performance Optimizations

The prototype intentionally avoids:
- caching,
- heuristics,
- acceleration,
- batching,
- ranking.

Performance pressure is the primary driver of architectural erosion.

This prototype resists that pressure by refusing optimization entirely.

---

## Constraint 7: Behavioral Observability Only

The system may be observed through:
- inputs,
- outputs,
- trajectories over time.

It must not expose:
- internal structures,
- invariants,
- lineage internals.

Continuity is inferred, not inspected.

---

## Constraint 8: Explicit Failure Over Silent Degradation

If a constraint is violated, the prototype should:
- fail loudly,
- raise errors,
- halt execution.

Silent degradation is the most dangerous failure mode.

---

## Summary

These constraints exist to ensure one thing only:

> **Reasoning identity can survive repeated inference only if reasoning is denied ownership of memory.**

Any system that feels the need to relax these constraints
is no longer attempting to preserve identity.

It is optimizing behavior instead.
