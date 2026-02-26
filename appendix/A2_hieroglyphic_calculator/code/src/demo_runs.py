# persistent-reasoning-architecture/appendix/A2_hieroglyphic_calculator/code/src/demo_runs.py
"""
Appendix A2 — Hieroglyphic Calculator
Demo runs producing deterministic, copy-pastable outputs.

This script is deliberately small and explicit:
- It runs a few canned scenarios
- Prints commit/reject events
- Writes transcripts under ./runs/ (optional, but recommended)

Scenarios:
1) run_01_valid      — normal transforms, stays within invariant envelope.
2) run_02_invalid    — injected drift (invalid constant / illegal transform id) -> reject.
3) run_03_wrong_path — demonstrates why a "solver-like" path is forbidden by policy.

Notes:
- This is NOT a CAS.
- The "wrong path solver" is intentionally fake: it shows the boundary violation,
  not a clever solver.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Tuple

from .checker import check_candidate
from .orchestrator_stub import A2Orchestrator, CombineFirstProposer, SimpleHeuristicProposer
from .state import InMemoryLineageStore, PRState, expr_add, expr_const, expr_mul
from .transforms import (
    FlattenAssociative,
    NormalizeOrdering,
    Transform,
    apply_transform_to_candidate,
)


RUNS_DIR = os.path.join(os.path.dirname(__file__), "..", "runs")


def _ensure_runs_dir() -> None:
    os.makedirs(RUNS_DIR, exist_ok=True)


def _write_transcript(filename: str, lines: List[str]) -> str:
    _ensure_runs_dir()
    path = os.path.join(RUNS_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")
    return path


def _banner(title: str) -> str:
    return f"{'='*8} {title} {'='*8}"


def _print_and_collect(lines: List[str], msg: str) -> None:
    print(msg)
    lines.append(msg)


def _setup_store_with_seed_expr(namespace: str, payload: Mapping[str, Any]) -> InMemoryLineageStore:
    store = InMemoryLineageStore()
    store.bootstrap(
        namespace=namespace,
        scope="A2:arithmetic:int",
        payload=dict(payload),
        meta={"parent_id": "GENESIS", "transform_id": "bootstrap"},
    )
    return store


# ------------------------------------------------------------
# Scenario 01 — Valid
# ------------------------------------------------------------

def run_01_valid() -> str:
    """
    A normal trajectory: flatten -> normalize -> combine-first proposer steps.
    We keep it deterministic and within the envelope.
    """
    ns = "A2:demo:valid"

    # Example expression: (2 + (2 + 3)) + 1
    payload = expr_add([expr_const(2), expr_add([expr_const(2), expr_const(3)]), expr_const(1)])

    store = _setup_store_with_seed_expr(ns, payload)

    transcript: List[str] = []
    _print_and_collect(transcript, _banner("RUN 01 — VALID"))

    # Phase 1: explicit flatten + normalize (manual, to show operations)
    head = store.head(ns)
    _print_and_collect(transcript, f"HEAD: {head.state_id} payload={head.payload}")

    for t in [FlattenAssociative("add"), NormalizeOrdering()]:
        cand = apply_transform_to_candidate(
            transform=t,
            scope=head.scope,
            payload=head.payload,
            parent_id=head.state_id,
        )
        check = check_candidate(cand)
        _print_and_collect(transcript, f"PROPOSE: {cand['meta']['transform_id']} -> check={check.ok} {check.reasons}")
        if check.ok:
            head = store.commit(ns, cand)
            _print_and_collect(transcript, f"COMMIT: {head.state_id}")
        else:
            _print_and_collect(transcript, "STOP: rejected unexpectedly")
            break

    # Phase 2: run orchestrator steps (combine-first proposer)
    orch = A2Orchestrator(store=store, namespace=ns, proposer=CombineFirstProposer())
    for i in range(5):
        committed, msg, st = orch.step()
        _print_and_collect(transcript, f"[orch step {i+1}] {msg}")
        if not committed:
            break

    final = store.head(ns)
    _print_and_collect(transcript, f"FINAL: {final.state_id} payload={final.payload}")

    path = _write_transcript("run_01_valid.txt", transcript)
    return path


# ------------------------------------------------------------
# Scenario 02 — Invalid drift (rejected)
# ------------------------------------------------------------

def run_02_invalid_drift() -> str:
    """
    Injects an invalid candidate:
    - illegal negative constant
    - solver-like transform id
    Both should be rejected by the checker.
    """
    ns = "A2:demo:invalid"

    # Start: 2 + 2
    payload = expr_add([expr_const(2), expr_const(2)])
    store = _setup_store_with_seed_expr(ns, payload)

    transcript: List[str] = []
    _print_and_collect(transcript, _banner("RUN 02 — INVALID DRIFT (REJECT)"))

    head = store.head(ns)
    _print_and_collect(transcript, f"HEAD: {head.state_id} payload={head.payload}")

    # Candidate 1: negative const (forbidden by A2 scope)
    bad_payload = expr_add([expr_const(2), expr_const(-1)])  # violates envelope
    cand1 = {
        "scope": head.scope,
        "payload": bad_payload,
        "meta": {"parent_id": head.state_id, "transform_id": "manual_inject"},
    }
    chk1 = check_candidate(cand1)
    _print_and_collect(transcript, f"PROPOSE: manual_inject payload={bad_payload}")
    _print_and_collect(transcript, f"CHECK: ok={chk1.ok} reasons={chk1.reasons}")
    _print_and_collect(transcript, "EXPECTED: reject\n")

    # Candidate 2: "solver-like" transform id (explicitly forbidden)
    cand2 = apply_transform_to_candidate(
        transform=NormalizeOrdering(),
        scope=head.scope,
        payload=head.payload,
        parent_id=head.state_id,
    )
    # mutate only the id to simulate a policy violation attempt
    cand2 = dict(cand2)
    cand2["meta"] = dict(cand2["meta"])
    cand2["meta"]["transform_id"] = "eval_and_solve_everything"  # forbidden marker

    chk2 = check_candidate(cand2)
    _print_and_collect(transcript, f"PROPOSE: {cand2['meta']['transform_id']}")
    _print_and_collect(transcript, f"CHECK: ok={chk2.ok} reasons={chk2.reasons}")
    _print_and_collect(transcript, "EXPECTED: reject")

    path = _write_transcript("run_02_invalid_drift.txt", transcript)
    return path


# ------------------------------------------------------------
# Scenario 03 — Wrong path: solver-like attempt (blocked)
# ------------------------------------------------------------

@dataclass(frozen=True)
class FakeSolverTransform:
    """
    A "transform" that tries to collapse the expression to a single constant.

    This is intentionally not a proper Transform implementation from transforms.py.
    We use it to demonstrate that "solver behavior" must be rejected by policy.
    """
    name: str = "fake_solver"
    transform_id: str = "solve_eval"  # should be flagged by checker as forbidden


def run_03_wrong_path_solver() -> str:
    """
    Shows how a solver-like attempt is prevented:
    - The candidate claims transform_id contains solve/eval.
    - Checker rejects it before it can be committed.
    """
    ns = "A2:demo:wrong_solver"

    # Start: (2 + 2) * 3  (tempting to evaluate to 12)
    payload = expr_mul([expr_add([expr_const(2), expr_const(2)]), expr_const(3)])
    store = _setup_store_with_seed_expr(ns, payload)

    transcript: List[str] = []
    _print_and_collect(transcript, _banner("RUN 03 — WRONG PATH (SOLVER-LIKE)"))

    head = store.head(ns)
    _print_and_collect(transcript, f"HEAD: {head.state_id} payload={head.payload}")

    # Fake solver proposes "evaluate everything"
    attempted_payload = expr_const(12)  # solver would collapse to this
    candidate = {
        "scope": head.scope,
        "payload": attempted_payload,
        "meta": {"parent_id": head.state_id, "transform_id": "solve_eval_all"},
    }
    chk = check_candidate(candidate)
    _print_and_collect(transcript, f"PROPOSE: solve_eval_all payload={attempted_payload}")
    _print_and_collect(transcript, f"CHECK: ok={chk.ok} reasons={chk.reasons}")

    if chk.ok:
        # Should not happen; but keep logic explicit.
        new_state = store.commit(ns, candidate)
        _print_and_collect(transcript, f"UNEXPECTED COMMIT: {new_state.state_id}")
    else:
        _print_and_collect(transcript, "EXPECTED: blocked before commit")

    _print_and_collect(transcript, "")
    _print_and_collect(transcript, "NOTE: This is the point of A2.")
    _print_and_collect(
        transcript,
        "The calculator boundary case is not about computing answers; it is about making certain drift paths architecturally illegal.",
    )

    path = _write_transcript("run_03_wrong_path_solver.txt", transcript)
    return path


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main() -> None:
    paths = []
    paths.append(run_01_valid())
    paths.append(run_02_invalid_drift())
    paths.append(run_03_wrong_path_solver())

    print("\n" + _banner("TRANSCRIPTS"))
    for p in paths:
        print(f"- {os.path.relpath(p, start=os.path.dirname(__file__))}")


if __name__ == "__main__":
    main()