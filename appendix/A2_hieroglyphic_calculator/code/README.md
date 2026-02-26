# Appendix 2 — Hieroglyphic Calculator


## Code Reference Implementation

This directory contains a **minimal academic reference implementation** of the Hieroglyphic Calculator used in Appendix 2.

It is not a solver.
It is not a CAS.
It is not a production-ready engine.

It is a structural demonstration of invariant-bound transformation control.


## Purpose of the Code

The code exists to demonstrate that:

- Invariants can be explicitly declared.
- Transformations can be strictly whitelisted.
- Invalid transformations can be deterministically rejected.
- State evolution can be append-only.
- Structural drift can be blocked before persistence.

This is a proof-of-boundary implementation.


## What This Code Does

The reference implementation:

- Defines a minimal state model.
- Registers allowed transformation rules.
- Evaluates invariants before accepting state transitions.
- Rejects invalid transformation attempts.
- Maintains append-only lineage of state changes.

It demonstrates invariant preservation under controlled transformation pressure.


## What This Code Does NOT Do

This code does not:

- Compute arithmetic results efficiently.
- Provide symbolic manipulation.
- Perform algebraic simplification.
- Auto-correct invalid steps.
- Learn new rules.
- Use LLM reasoning.
- Perform semantic equivalence checks.
- Support concurrent governance.

Primitive computation must be delegated to deterministic external systems (see Appendix 3).


## Architectural Position

This code sits inside:

Persistent Reasoning → Appendix 2 → Academic Boundary Case.

It supports:

- Invariant preservation.
- Transformation admissibility enforcement.
- Explicit governance discipline.

It does not redefine:

- Solver logic.
- Domain mathematics.
- Reasoning orchestration.


## Execution Model

The typical flow is:

1. Construct initial state.
2. Attempt a transformation.
3. Validate:
   - Is transformation registered?
   - Are invariants preserved?
4. If valid → append state.
5. If invalid → reject without mutation.

All state changes are explicit.
No implicit mutation is allowed.


## Design Constraints

- Deterministic behavior.
- No randomness.
- No hidden side effects.
- No silent state rewrite.
- No implicit canonicalization beyond defined rules.

If behavior appears “too simple,” that is intentional.


## Why This Implementation Is Minimal

Appendix 2 is an academic boundary case.

Its goal is to prove:

Invalid reasoning can be made structurally non-admissible.

It is intentionally:

- Small.
- Constrained.
- Underpowered by design.

Any attempt to extend this into a solver would violate its purpose.


## Relationship to Other Appendices

Appendix 0 — Identity Skeleton  
→ Proof of boundary.

Appendix 1 — Identity Formalization & Merge  
→ Proof of structural consistency.

Appendix 2 — Hieroglyphic Calculator  
→ Proof of invariant preservation.

Appendix 3 — Reasoning Orchestrator  
→ Delegation of primitive computation to external systems.


## Important Warning

Do not treat this code as a computational engine.

If you need:
- Correct arithmetic,
- Algebra,
- Theorem proving,
- Numerical simulation,

You must use external deterministic systems and keep Persistent Reasoning as the governance layer.


## Closing

This code does not make systems smarter.

It demonstrates how to prevent structural drift from becoming persistent policy.