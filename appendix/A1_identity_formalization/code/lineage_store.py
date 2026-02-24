# Copyright (c) 2026 Vladislav Bliznyukov
# Licensed under the MIT License.
# persistent-reasoning-architecture/appendix/A1_identity_formalization/code/lineage_store.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Set, Tuple
import time
import uuid


class LineageError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class Commit:
    """
    Append-only commit record.

    Important:
    - This is NOT a mutable database row.
    - Commits are immutable events.
    - 'payload' is opaque to the store (store never evaluates it).
    """
    commit_id: str
    timestamp_ms: int
    parents: Tuple[str, ...]
    op: str  # add | replace | forget | merge | milestone | loss_marker | replay_marker
    subject_id: str  # IdentityAnchor.id (or equivalent identifier string)
    subject_kind: str
    subject_namespace: str
    subject_scope: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    note: str = ""


@dataclass
class LineageStore:
    """
    Minimal in-memory append-only lineage store.
    This is a toy, but it enforces the correct *shape*:
      - append-only commit log
      - parent pointers
      - no in-place mutation
      - no query interface for satisfaction/entailment
    """
    _commits: Dict[str, Commit] = field(default_factory=dict)
    _children: Dict[str, Set[str]] = field(default_factory=dict)

    def append(
        self,
        *,
        parents: Iterable[str],
        op: str,
        subject_id: str,
        subject_kind: str,
        subject_namespace: str,
        subject_scope: str,
        payload: Optional[Mapping[str, Any]] = None,
        note: str = "",
    ) -> Commit:
        parent_ids = tuple(parents)
        for p in parent_ids:
            if p not in self._commits:
                raise LineageError(f"unknown parent commit: {p}")

        commit_id = uuid.uuid4().hex
        ts = int(time.time() * 1000)

        c = Commit(
            commit_id=commit_id,
            timestamp_ms=ts,
            parents=parent_ids,
            op=op,
            subject_id=subject_id,
            subject_kind=subject_kind,
            subject_namespace=subject_namespace,
            subject_scope=subject_scope,
            payload=dict(payload or {}),
            note=note,
        )
        self._commits[commit_id] = c
        for p in parent_ids:
            self._children.setdefault(p, set()).add(commit_id)
        self._children.setdefault(commit_id, set())
        return c

    def get(self, commit_id: str) -> Commit:
        if commit_id not in self._commits:
            raise LineageError(f"unknown commit id: {commit_id}")
        return self._commits[commit_id]

    def exists(self, commit_id: str) -> bool:
        return commit_id in self._commits

    def all_commits(self) -> List[Commit]:
        # Deterministic order for demos: timestamp then commit_id
        return sorted(self._commits.values(), key=lambda c: (c.timestamp_ms, c.commit_id))

    def children_of(self, commit_id: str) -> Set[str]:
        if commit_id not in self._children:
            return set()
        return set(self._children[commit_id])

    def ancestors_of(self, commit_id: str) -> Set[str]:
        """
        Return all ancestor commits of a given commit id.
        This is lineage navigation, not a semantic query.
        """
        if commit_id not in self._commits:
            raise LineageError(f"unknown commit id: {commit_id}")

        visited: Set[str] = set()
        stack: List[str] = [commit_id]
        while stack:
            cur = stack.pop()
            for p in self._commits[cur].parents:
                if p not in visited:
                    visited.add(p)
                    stack.append(p)
        return visited

    def lca_candidates(self, a: str, b: str) -> Set[str]:
        """
        Lowest common ancestor candidates: intersection of ancestor sets plus
        the nodes themselves if applicable. Not necessarily unique.
        """
        if a not in self._commits or b not in self._commits:
            raise LineageError("unknown commit id(s)")
        anc_a = self.ancestors_of(a) | {a}
        anc_b = self.ancestors_of(b) | {b}
        return anc_a & anc_b
