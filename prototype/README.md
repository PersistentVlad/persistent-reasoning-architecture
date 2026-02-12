# Prototype: Minimal Persistent Reasoning System

## What This Is

This directory contains a **minimal executable prototype** of a persistent reasoning architecture.

It is **not**:
- a product,
- a framework,
- an agent system,
- a performance demo,
- a learning system,
- or a practical solution to real-world tasks.

It **is**:
- an executable boundary,
- a proof of architectural discipline,
- a demonstration that persistent reasoning can exist **only under strict constraints**.

If this prototype feels *underpowered*, *limited* or *unsatisfying* — **that is by design**.

---

## Reading Order and Map
```
prototype/
├── !README.md
├── design_constraints.md
├── minimal_components.md
├── execution_loop.md
├── what_this_prototype_cannot_do.md
├── collapse_if_extended.md
└── prototype_code/
    ├── __init__.py
    ├── persistent_store.py
    ├── write_barrier.py
    ├── proposal_engine.py
    ├── commit_gate.py
    ├── inference_stub.py
    └── run_minimal_loop.py
```
---

## Why This Prototype Exists

Most AI prototypes attempt to demonstrate capability.

This one demonstrates **constraint survival**.

The goal is not to show that the system can:
- solve tasks better,
- reason faster,
- generalize wider,
- or outperform baselines.

The goal is to show that:

> **Reasoning identity can persist across inference events only if reasoning is denied ownership of memory.**

This prototype answers a single question:

> *Can a persistent reasoning structure exist in executable form without collapsing into querying, learning or optimization?*

The answer demonstrated here is: **yes — but only barely**.

---

## Core Architectural Commitments

This prototype enforces the following commitments **by construction**, not by convention:

- **Write Authority Is Singular**
  - All mutation of persistent structures passes through a single write barrier.
  - Inference code has no write access.

- **No Queryability**
  - Persistent structures cannot be queried, solved, evaluated or satisfied.
  - They can only be navigated and compared structurally.

- **Append-Only Persistence**
  - No in-place updates.
  - Identity lives in lineage, not in snapshots.

- **Proposal ≠ Commitment**
  - Inference may propose changes.
  - Commitment is a separate, deliberate operation.

- **No Learning**
  - There is no gradient descent, reinforcement or implicit adaptation.
  - Persistence is achieved through explicit revision only.

If any of these constraints are relaxed, the architecture collapses into familiar failure modes.

---

## What This Prototype Is Explicitly Not Trying To Do

This prototype does **not** attempt to:

- demonstrate intelligence,
- demonstrate correctness,
- demonstrate accuracy,
- demonstrate optimality,
- demonstrate learning,
- demonstrate performance,
- demonstrate scalability.

Any attempt to extend this prototype toward those goals **without architectural redesign** will result in silent collapse.

This is intentional.

---

## Why the Prototype Is So Small

Persistent reasoning is not hard because it requires complexity.

It is hard because it requires **refusal**.

Most systems fail not because they lack mechanisms,
but because they allow too many operations.

This prototype is small because:
- every extra capability is a potential collapse path,
- minimality makes violations visible,
- discipline is easier to audit than cleverness.

---

## How to Read This Prototype

This is not a reference implementation.

Read it as you would read:
- a minimal transactional system,
- a memory consistency litmus test,
- or a proof-of-possibility in systems research.

The most important files are not the ones that *do things*,
but the ones that explain **why things are forbidden**.

---

## If You Feel the Urge to Improve It

That urge is expected.

Before doing so, ask yourself:

- Does this introduce queryability?
- Does this give inference indirect write authority?
- Does this optimize behavior instead of preserving tension?
- Does this collapse identity into state?
- Does this turn persistence into learning?

If the answer to any is “yes” —
you are no longer working on persistent reasoning.

You are building something else.

---

## Relationship to the Rest of the Repository

This prototype is the executable counterpart to:

- `docs/practical/p7_minimal_executable_architecture.md`
- `docs/governance/architectural_discipline.md`
- `docs/appendix/collapse_modes.md`

It exists to make the architectural claims **testable**, not impressive.

---

## Final Warning

This prototype will not make your system smarter.

It may, however, make it **capable of remembering how it reasons** —
which is a different property entirely.

That distinction is the point of this repository.
