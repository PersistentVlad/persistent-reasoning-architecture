# Copyright (c) 2026 Vladislav Bliznyukov
# Licensed under the MIT License.
# persistent-reasoning-architecture/appendix/A1_identity_formalization/code/demo_merge_scenarios.py

from __future__ import annotations

"""
Appendix A1 — Identity Formalization & Merge Scenarios (code)

What this script demonstrates (at a toy level):
- Append-only lineage with branching
- Identity anchors derived from canonicalized payloads
- Three-way merge *analysis* (structural, not semantic)
- Collision / mismatch detection patterns

Run:
  python demo_merge_scenarios.py

Note:
- This demo intentionally avoids "solving" anything.
- It only navigates lineage and compares canonical forms.
"""

from typing import Any, Dict, Mapping, Tuple

from lineage_store import LineageStore
from identity import IdentityAnchor
from merge_engine import (
    three_way_merge_analysis,
    commit_merge,
    detect_identity_collision,
)


def _print_commit(c) -> None:
    parents = ",".join(c.parents) if c.parents else "-"
    print(
        f"- {c.commit_id[:8]}  op={c.op:<8}  subject={c.subject_id[:12]}  "
        f"parents={parents[:20]}  note={c.note}"
    )


def _print_header(title: str) -> None:
    print("\n" + "=" * len(title))
    print(title)
    print("=" * len(title))


def _payload(statement: str, *, tensions: Tuple[str, ...] = ()) -> Dict[str, Any]:
    # Toy "structural motif" payload (still just a dict)
    return {
        "statement": statement,
        "tensions": list(tensions),
        "metadata": {
            "format": "toy",
            "role": "structural_payload",
        },
    }


def _seed(store: LineageStore) -> str:
    # A genesis commit with a dummy subject.
    genesis_anchor = IdentityAnchor.create(
        kind="motif",
        namespace="A1.demo",
        scope="global",
        payload=_payload("GENESIS"),
    )
    genesis = store.append(
        parents=(),
        op="milestone",
        subject_id=genesis_anchor.id,
        subject_kind=genesis_anchor.kind,
        subject_namespace=genesis_anchor.namespace,
        subject_scope=genesis_anchor.scope,
        payload={"milestone": "genesis"},
        note="genesis",
    )
    return genesis.commit_id


def _branch_left(store: LineageStore, base: str) -> str:
    """
    Left branch:
      - add motif A
      - refine motif A (replace)
      - add motif B
    """
    a1 = _payload("Never let inference write persistence.", tensions=("speed vs stability",))
    anchor_a = IdentityAnchor.create(kind="motif", namespace="A1.demo", scope="global", payload=a1)

    c1 = store.append(
        parents=(base,),
        op="add",
        subject_id=anchor_a.id,
        subject_kind=anchor_a.kind,
        subject_namespace=anchor_a.namespace,
        subject_scope=anchor_a.scope,
        payload=a1,
        note="L: add motif A",
    )

    a2 = _payload(
        "Never let inference write persistence (write barrier is non-negotiable).",
        tensions=("speed vs stability", "convenience vs discipline"),
    )
    # Replace means new identity (explicit); in PR, mutation is versioned, not in-place.
    anchor_a2 = IdentityAnchor.create(kind="motif", namespace="A1.demo", scope="global", payload=a2)

    c2 = store.append(
        parents=(c1.commit_id,),
        op="replace",
        subject_id=anchor_a2.id,
        subject_kind=anchor_a2.kind,
        subject_namespace=anchor_a2.namespace,
        subject_scope=anchor_a2.scope,
        payload=a2,
        note="L: replace motif A -> A2",
    )

    b1 = _payload("Append-only lineage defines identity boundaries.", tensions=("storage cost vs auditability",))
    anchor_b = IdentityAnchor.create(kind="motif", namespace="A1.demo", scope="global", payload=b1)

    c3 = store.append(
        parents=(c2.commit_id,),
        op="add",
        subject_id=anchor_b.id,
        subject_kind=anchor_b.kind,
        subject_namespace=anchor_b.namespace,
        subject_scope=anchor_b.scope,
        payload=b1,
        note="L: add motif B",
    )
    return c3.commit_id


def _branch_right(store: LineageStore, base: str, *, force_conflict: bool) -> str:
    """
    Right branch:
      - add motif A (same initial statement)
      - maybe refine motif A differently (conflict)
      - add motif C
    """
    a1 = _payload("Never let inference write persistence.", tensions=("speed vs stability",))
    anchor_a = IdentityAnchor.create(kind="motif", namespace="A1.demo", scope="global", payload=a1)

    c1 = store.append(
        parents=(base,),
        op="add",
        subject_id=anchor_a.id,
        subject_kind=anchor_a.kind,
        subject_namespace=anchor_a.namespace,
        subject_scope=anchor_a.scope,
        payload=a1,
        note="R: add motif A",
    )

    if force_conflict:
        a_alt = _payload(
            "Avoid direct writes from inference; prefer governance commits.",
            tensions=("iteration speed vs correctness",),
        )
        anchor_alt = IdentityAnchor.create(kind="motif", namespace="A1.demo", scope="global", payload=a_alt)

        c2 = store.append(
            parents=(c1.commit_id,),
            op="replace",
            subject_id=anchor_alt.id,
            subject_kind=anchor_alt.kind,
            subject_namespace=anchor_alt.namespace,
            subject_scope=anchor_alt.scope,
            payload=a_alt,
            note="R: replace motif A -> A_alt (diverges)",
        )
        head = c2.commit_id
    else:
        head = c1.commit_id

    c1p = _payload("Non-queryability is a design property, not a policy.", tensions=("debuggability vs collapse risk",))
    anchor_c = IdentityAnchor.create(kind="motif", namespace="A1.demo", scope="global", payload=c1p)

    c3 = store.append(
        parents=(head,),
        op="add",
        subject_id=anchor_c.id,
        subject_kind=anchor_c.kind,
        subject_namespace=anchor_c.namespace,
        subject_scope=anchor_c.scope,
        payload=c1p,
        note="R: add motif C",
    )
    return c3.commit_id


def _scenario_no_conflict() -> None:
    _print_header("Scenario 1: Branches add different motifs (no direct conflicts)")
    store = LineageStore()
    base = _seed(store)
    left = _branch_left(store, base)
    right = _branch_right(store, base, force_conflict=False)

    print("\nLineage (all commits):")
    for c in store.all_commits():
        _print_commit(c)

    decision = three_way_merge_analysis(store=store, left_head=left, right_head=right)
    print("\nMerge analysis actions:")
    for a in decision.actions:
        print("  -", dict(a))
    print("\nMerge analysis conflicts:")
    for c in decision.conflicts:
        print("  -", dict(c))

    # Provide explicit merged payloads (governance choice).
    # Here we accept all actions and produce a merged set:
    merged: Dict[str, Mapping[str, Any]] = {}
    # We simply pick "latest" payloads from each side per action.
    # (This is governance choosing, not automatic solver logic.)
    latest = {c.commit_id: c for c in store.all_commits()}
    for a in decision.actions:
        if a["proposal"] in ("accept_left", "accept_right", "accept_either"):
            if a["proposal"] == "accept_left":
                merged[a["subject_id"]] = latest[a["left_commit"]].payload
            elif a["proposal"] == "accept_right":
                merged[a["subject_id"]] = latest[a["right_commit"]].payload
            else:
                # accept either; choose left arbitrarily for demo
                merged[a["subject_id"]] = latest[a["left_commit"]].payload

    merge_commits = commit_merge(
        store=store,
        parents=(left, right),
        decision=decision,
        merged_subject_payloads=merged,
        kind="motif",
        namespace="A1.demo",
        scope="global",
        note="MERGE: scenario 1",
    )

    print("\nMerge commits created:")
    for c in merge_commits:
        _print_commit(c)


def _scenario_conflict() -> None:
    _print_header("Scenario 2: Divergent updates (structural conflict requiring explicit decision)")
    store = LineageStore()
    base = _seed(store)
    left = _branch_left(store, base)
    right = _branch_right(store, base, force_conflict=True)

    decision = three_way_merge_analysis(store=store, left_head=left, right_head=right)

    print("\nMerge analysis actions:")
    for a in decision.actions:
        print("  -", dict(a))
    print("\nMerge analysis conflicts:")
    for c in decision.conflicts:
        print("  -", dict(c))

    if decision.conflicts:
        print("\nGovernance note:")
        print("  Conflicts cannot be auto-resolved. Choose explicitly:")
        print("  - accept_left")
        print("  - accept_right")
        print("  - replace (create new anchor and supersede both)")
        print("  - keep both (branch-aware coexistence)")

    # For the demo, we resolve conflicts by "keep both" via explicit replace:
    # Create a new combined motif payload capturing the tension explicitly.
    resolved: Dict[str, Mapping[str, Any]] = {}
    latest_by_commit = {c.commit_id: c for c in store.all_commits()}

    # Apply non-conflicting actions
    for a in decision.actions:
        if a["proposal"] == "accept_left":
            resolved[a["subject_id"]] = latest_by_commit[a["left_commit"]].payload
        elif a["proposal"] == "accept_right":
            resolved[a["subject_id"]] = latest_by_commit[a["right_commit"]].payload
        elif a["proposal"] == "accept_either":
            resolved[a["subject_id"]] = latest_by_commit[a["left_commit"]].payload

    # Resolve conflict by introducing a new motif (new identity).
    if decision.conflicts:
        conflict = decision.conflicts[0]
        new_payload = _payload(
            "Write barrier: prohibit inference writes; governance commits only (captures both framings).",
            tensions=("speed vs stability", "iteration vs correctness"),
        )
        # New anchor will be created inside commit_merge; we just provide payload.
        # We'll map it under a *placeholder key*; commit_merge will turn it into replace.
        placeholder_subject_id = conflict["subject_id"]
        resolved[placeholder_subject_id] = new_payload

    merge_commits = commit_merge(
        store=store,
        parents=(left, right),
        decision=decision,
        merged_subject_payloads=resolved,
        kind="motif",
        namespace="A1.demo",
        scope="global",
        note="MERGE: scenario 2 (explicit resolution)",
    )

    print("\nMerge commits created:")
    for c in merge_commits:
        _print_commit(c)


def _scenario_collision_detection() -> None:
    _print_header("Scenario 3: Identity collision / mismatch detection")
    # Create an anchor from payload P, then observe payload Q under the same claimed anchor id.
    p = _payload("Scope-first: persistence is bounded by scope.")
    q = _payload("Scope-first: persistence is bounded by scope (but secretly changed).")

    anchor = IdentityAnchor.create(kind="motif", namespace="A1.demo", scope="global", payload=p)

    reason = detect_identity_collision(anchor=anchor, expected_payload=p, observed_payload=q)
    print("Anchor id:", anchor.id)
    print("Collision detected?" , "YES" if reason else "NO")
    if reason:
        print("Reason:", reason)


def main() -> None:
    _scenario_no_conflict()
    _scenario_conflict()
    _scenario_collision_detection()


if __name__ == "__main__":
    main()
