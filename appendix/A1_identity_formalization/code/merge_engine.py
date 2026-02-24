# Copyright (c) 2026 Vladislav Bliznyukov
# Licensed under the MIT License.
# persistent-reasoning-architecture/appendix/A1_identity_formalization/code/merge_engine.py

# NOTE:
# This merge analysis assumes serialized commit decisions.
# Concurrent governance is intentionally out of scope.

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

from .identity import IdentityAnchor, IdentityError
from .canonicalization import canonicalize_payload, CanonicalizationError
from .lineage_store import LineageStore, Commit, LineageError


class MergeError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class MergeDecision:
    """
    Output of merge analysis.
    This is intentionally *not* an automatic resolver; it is a decision artifact.
    """
    base_commit: Optional[str]
    left_commit: str
    right_commit: str
    actions: Tuple[Mapping[str, Any], ...]
    conflicts: Tuple[Mapping[str, Any], ...]
    note: str = ""


def _index_latest_by_subject(commits: Sequence[Commit]) -> Dict[str, Commit]:
    """
    For a linear chain demo, "latest" is last commit per subject_id.
    In real systems you'd compute heads or materialized views.
    """
    out: Dict[str, Commit] = {}
    for c in commits:
        out[c.subject_id] = c
    return out


def _commit_chain(store: LineageStore, head: str) -> List[Commit]:
    """
    Follow parents assuming a single-parent linear chain (toy).
    If multiple parents exist, we stop (merge commit) to avoid inventing policy.
    """
    chain: List[Commit] = []
    cur = head
    while True:
        c = store.get(cur)
        chain.append(c)
        if len(c.parents) != 1:
            break
        cur = c.parents[0]
    chain.reverse()
    return chain


def _pick_base(store: LineageStore, left: str, right: str) -> Optional[str]:
    """
    Pick a base commit for a 3-way merge.
    In real systems: choose the LCA with maximal depth / recency.
    Here: choose the newest timestamp among LCA candidates.
    """
    cands = store.lca_candidates(left, right)
    if not cands:
        return None
    best = None
    best_key = None
    for cid in cands:
        c = store.get(cid)
        key = (c.timestamp_ms, cid)
        if best is None or key > best_key:
            best = cid
            best_key = key
    return best


def _semantic_free_payload_change(commit: Commit) -> str:
    """
    A stable representation of what changed, without interpreting it.
    Used only for structural diffing / collision detection.
    """
    try:
        return canonicalize_payload(commit.payload)
    except CanonicalizationError:
        # If payload can't be canonicalized, we still must not interpret it.
        # We treat it as "opaque changed" marker.
        return "<opaque-payload>"


def detect_identity_collision(
    *,
    anchor: IdentityAnchor,
    expected_payload: Mapping[str, Any],
    observed_payload: Mapping[str, Any],
) -> Optional[str]:
    """
    Detect: same anchor id but payload differs => collision or unauthorized mutation.

    Returns a human-readable reason, or None if no collision detected.
    """
    try:
        expected_id = IdentityAnchor.create(
            kind=anchor.kind,
            namespace=anchor.namespace,
            scope=anchor.scope,
            payload=expected_payload,
            version=anchor.version,
        ).id
    except IdentityError as e:
        return f"cannot reconstruct expected anchor: {e}"

    if expected_id != anchor.id:
        # Not a collision, but mismatch between "anchor" and "expected payload".
        return "anchor mismatch: expected payload does not reconstruct the given anchor id"

    # Now, check if observed payload reconstructs the same anchor id.
    try:
        observed_id = IdentityAnchor.create(
            kind=anchor.kind,
            namespace=anchor.namespace,
            scope=anchor.scope,
            payload=observed_payload,
            version=anchor.version,
        ).id
    except IdentityError as e:
        return f"cannot reconstruct observed anchor: {e}"

    if observed_id != anchor.id:
        return (
            "identity collision (or unauthorized mutation): "
            "same anchor id, but observed payload does not reconstruct it"
        )
    return None


def three_way_merge_analysis(
    *,
    store: LineageStore,
    left_head: str,
    right_head: str,
) -> MergeDecision:
    """
    Analyze a merge without automatically resolving conflicts.

    This function produces:
    - 'actions': safe proposals (e.g., 'keep left change', 'keep right change', 'introduce rename')
    - 'conflicts': ambiguous/unsafe areas requiring explicit decision

    It respects the PR stance:
    - merge is governance, not inference
    - no hidden semantic solving
    - only structural comparisons and lineage navigation
    """
    if not store.exists(left_head) or not store.exists(right_head):
        raise MergeError("left_head or right_head does not exist in store")

    base = _pick_base(store, left_head, right_head)

    # Build commit chains (toy linear assumption).
    left_chain = _commit_chain(store, left_head)
    right_chain = _commit_chain(store, right_head)
    base_commit = store.get(base) if base else None

    # Build "latest per subject" snapshots for each side.
    left_latest = _index_latest_by_subject(left_chain)
    right_latest = _index_latest_by_subject(right_chain)
    base_latest = _index_latest_by_subject(_commit_chain(store, base)) if base else {}

    actions: List[Mapping[str, Any]] = []
    conflicts: List[Mapping[str, Any]] = []

    all_subjects: Set[str] = set(left_latest) | set(right_latest) | set(base_latest)

    for sid in sorted(all_subjects):
        l = left_latest.get(sid)
        r = right_latest.get(sid)
        b = base_latest.get(sid)

        # Only in one side: safe propose to accept that side's version.
        if l and not r:
            actions.append(
                {
                    "subject_id": sid,
                    "proposal": "accept_left",
                    "reason": "subject appears only on left branch",
                    "left_commit": l.commit_id,
                }
            )
            continue
        if r and not l:
            actions.append(
                {
                    "subject_id": sid,
                    "proposal": "accept_right",
                    "reason": "subject appears only on right branch",
                    "right_commit": r.commit_id,
                }
            )
            continue

        assert l and r  # both exist

        # If payload canonical forms match, safe: no conflict.
        l_sig = _semantic_free_payload_change(l)
        r_sig = _semantic_free_payload_change(r)
        if l_sig == r_sig:
            actions.append(
                {
                    "subject_id": sid,
                    "proposal": "accept_either",
                    "reason": "structurally equivalent payload changes",
                    "left_commit": l.commit_id,
                    "right_commit": r.commit_id,
                }
            )
            continue

        # If base exists and one side equals base, accept the other side.
        if b:
            b_sig = _semantic_free_payload_change(b)
            if l_sig == b_sig and r_sig != b_sig:
                actions.append(
                    {
                        "subject_id": sid,
                        "proposal": "accept_right",
                        "reason": "left matches base; right diverges",
                        "base_commit": b.commit_id,
                        "right_commit": r.commit_id,
                    }
                )
                continue
            if r_sig == b_sig and l_sig != b_sig:
                actions.append(
                    {
                        "subject_id": sid,
                        "proposal": "accept_left",
                        "reason": "right matches base; left diverges",
                        "base_commit": b.commit_id,
                        "left_commit": l.commit_id,
                    }
                )
                continue

        # Divergence on both sides => governance conflict.
        conflicts.append(
            {
                "subject_id": sid,
                "conflict": "divergent_updates",
                "reason": "both branches diverged for same subject_id; requires explicit merge policy",
                "base_commit": b.commit_id if b else None,
                "left_commit": l.commit_id,
                "right_commit": r.commit_id,
                "left_payload_sig": l_sig,
                "right_payload_sig": r_sig,
            }
        )

    note = (
        "This is a structural merge analysis (no semantic resolution). "
        "Conflicts must be resolved by explicit revision decisions."
    )
    return MergeDecision(
        base_commit=base,
        left_commit=left_head,
        right_commit=right_head,
        actions=tuple(actions),
        conflicts=tuple(conflicts),
        note=note,
    )


def commit_merge(
    *,
    store: LineageStore,
    parents: Tuple[str, str],
    decision: MergeDecision,
    merged_subject_payloads: Mapping[str, Mapping[str, Any]],
    kind: str,
    namespace: str,
    scope: str = "global",
    note: str = "merge commit",
) -> List[Commit]:
    """
    Apply a merge decision by creating new commits for merged subjects.

    Important:
    - This does NOT attempt to compute merges automatically.
    - Caller provides merged payloads per subject_id after explicit resolution.

    For each subject_id payload, we:
    - reconstruct an anchor and ensure it matches the provided subject_id
      OR create a 'replace' that supersedes prior identity (rename / new anchor)
    """
    left, right = parents
    if not store.exists(left) or not store.exists(right):
        raise MergeError("merge parents must exist")

    merge_commits: List[Commit] = []
    for subject_id, payload in merged_subject_payloads.items():
        # Create anchor from payload; if it doesn't match, treat as "replace/rename".
        anchor = IdentityAnchor.create(kind=kind, namespace=namespace, scope=scope, payload=payload)
        if anchor.id == subject_id:
            op = "merge"
            sid = subject_id
        else:
            # Identity changed: must be explicit.
            op = "replace"
            sid = anchor.id

        c = store.append(
            parents=(left, right),
            op=op,
            subject_id=sid,
            subject_kind=kind,
            subject_namespace=namespace,
            subject_scope=scope,
            payload=payload,
            note=note,
        )
        merge_commits.append(c)

    return merge_commits
