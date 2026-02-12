# Copyright (c) 2026 Vladislav Bliznyukov
# Licensed under the MIT License.

"""
run_minimal_loop.py

A minimal executable loop wiring together:
- PersistentStore (append-only structure)
- WriteBarrier (single write authority + invariants)
- InferenceStub (execution role)
- ProposalEngine (proposer role)
- CommitGate (governance role)

This is a demonstrator, not a system.

What it shows:
- Inference consumes structure but cannot mutate it.
- Proposals are generated from observations, but are not persistence.
- Commit is deliberate, policy-gated and goes through the write barrier.
- Version lineage is append-only; identity lives in the chain.

It intentionally avoids:
- real task solving
- querying structures
- optimization loops
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .persistent_store import PersistentStore, minimal_motif_payload
from .write_barrier import WriteBarrier
from .proposal_engine import ProposalEngine, ProposalContext
from .commit_gate import CommitGate, CommitPolicy
from .inference_stub import InferenceStub, TaskInput


@dataclass(frozen=True)
class DemoTask:
    task_id: str
    prompt: str


def run_demo(iterations: int = 8) -> None:
    # 1) Initialize persistence (a single motif for the demo)
    store = PersistentStore()
    motif_id = "motif:core"

    initial = minimal_motif_payload(
        tensions=[
            "flexibility ↔ discipline",
            "local success ↔ long-term coherence",
        ],
        notes="Initial motif for minimal executable demo.",
    )
    v0 = store.create_motif(motif_id, initial, meta={"actor": "bootstrap", "commit_message": "init"})

    # 2) Build the architecture roles
    barrier = WriteBarrier(store)
    proposer = ProposalEngine(seed=7)
    gate = CommitGate(store, barrier, policy=CommitPolicy(commit_probability=0.35, min_iterations_between_commits=2), seed=11)
    inference = InferenceStub()

    # 3) Demo tasks (intentionally simple prompts to generate observations)
    tasks: List[DemoTask] = [
        DemoTask("t1", "Plan a fast response under latency pressure."),
        DemoTask("t2", "Do it cheaper; budget is tight."),
        DemoTask("t3", "Now prioritize safety; risk is high."),
        DemoTask("t4", "Be accurate; correctness matters."),
        DemoTask("t5", "User trust is fragile; do not drift."),
        DemoTask("t6", "Mixed pressure: fast + safe + accurate."),
    ]

    print("=== Minimal Executable Persistent Reasoning Loop (Demo) ===")
    print(f"Start version: {v0.version_id}")
    print()

    # 4) Loop
    for i in range(iterations):
        task = tasks[i % len(tasks)]
        latest = store.latest_version(motif_id)

        # Inference consumes structure
        out = inference.run(latest, TaskInput(task.task_id, task.prompt))

        # Proposal generation (from observations)
        cand = proposer.propose_revision(
            latest,
            ProposalContext(task_id=out.task_id, observation=out.observations),
        )

        # Governance decides whether to commit (after barrier validation)
        res = gate.consider(
            motif_id=motif_id,
            proposal_payload=cand.proposed_payload,
            rationale=cand.rationale,
            iteration=i,
            actor="commit-gate",
        )

        # Print a small trace
        print(f"--- iter={i} task={task.task_id} ---")
        print(out.answer)
        print(f"[obs] {out.observations}")
        print(f"[proposal] {cand.rationale}")

        if res.accepted and res.new_version is not None:
            print(f"[commit] ACCEPTED -> new_version={res.new_version.version_id}")
        else:
            print(f"[commit] REJECTED -> reason={res.reason}")

        print(f"[lineage_len] {len(store.lineage(motif_id))}")
        print()

    # 5) Show lineage summary
    print("=== Final Lineage ===")
    for mv in store.lineage(motif_id):
        msg = mv.meta.get("commit_message", "")
        actor = mv.meta.get("actor", "")
        print(f"- {mv.version_id} (actor={actor}, msg={msg})")


if __name__ == "__main__":
    run_demo()
