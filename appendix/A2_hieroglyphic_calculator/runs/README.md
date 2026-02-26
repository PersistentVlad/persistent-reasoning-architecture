# Appendix 2 — Hieroglyphic Calculator  
## Runs (Deterministic Transcripts)

This directory contains deterministic transcripts produced by:

code/src/demo_runs.py

The goal of these runs is not to demonstrate performance or correctness of arithmetic.
The goal is to demonstrate structural behavior of the invariant envelope.

---

## Purpose of These Runs

Each run illustrates one architectural point:

- What a valid structural evolution looks like.
- How invariant violations are detected and rejected.
- Why solver-like shortcuts are forbidden.
- How the system blocks structural drift before commit.

These transcripts are part of the academic boundary proof.

---

## Run Descriptions

### run_01_valid.txt

Demonstrates:

- Controlled transformations (flatten, normalize, combine).
- Invariant checks before commit.
- Append-only lineage behavior.
- Deterministic evolution of structure.

No evaluation collapse occurs.
The expression remains structured.

This is the "allowed path".

---

### run_02_invalid_drift.txt

Demonstrates rejection of:

- Negative constants (outside A2 scope).
- Illegal transform identifiers (solver-like behavior).

The checker blocks the candidate before commit.

This is the "blocked drift path".

---

### run_03_wrong_path_solver.txt

Demonstrates:

- A fake solver attempt collapsing a structured expression into a constant.
- Explicit rejection due to forbidden transform id.

This is the architectural boundary:

The calculator is not allowed to behave like a solver.

---

## How to Reproduce

From inside the A2 code directory:

```bash
python -m src.demo_runs
```
Transcripts will be written into this directory.
What These Runs Prove
They prove that:
Invalid structural mutations can be blocked deterministically.
Solver-like collapse can be detected at policy level.
State transitions require admissibility checks before persistence.
The envelope protects identity continuity.
They do not prove:
Mathematical correctness.
Solver completeness.
Computational efficiency.
Semantic equivalence.
Important Clarification
These runs are intentionally simple.
They are not benchmarks. They are not evaluation metrics. They are not performance demonstrations.
They are structural behavior demonstrations.
Appendix 2 is an academic boundary case.
Its purpose is to show how invariants survive transformation pressure — not how to solve arithmetic.