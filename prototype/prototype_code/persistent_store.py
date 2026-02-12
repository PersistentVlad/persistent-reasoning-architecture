# Copyright (c) 2026 Vladislav Bliznyukov
# Licensed under the MIT License.

"""
persistent_store.py

A minimal append-only store for Persistent Reasoning structures.

Key properties enforced by design:
- Append-only versions (no in-place mutation)
- No query API (structures are not "solved" or "satisfied")
- Read-only access returns immutable snapshots
- Identity lives in lineage (version chain), not in current state

This is NOT a database, NOT a knowledge graph store and NOT an inference substrate.
It preserves identity, not answers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple
import hashlib
import json
import time


class NonQueryabilityViolation(RuntimeError):
    """Raised when a forbidden query-like operation is attempted."""


class StoreInvariantViolation(RuntimeError):
    """Raised when append-only / lineage invariants are violated."""


@dataclass(frozen=True)
class MotifVersion:
    """
    Immutable snapshot of a reasoning structure (motif) at a specific version.

    Note: the structure payload is intentionally generic (JSON-serializable dict).
    The store does not interpret semantics and offers no query interface.
    """
    motif_id: str
    version_id: str
    parent_version_id: Optional[str]
    created_at_unix: float
    payload: Dict
    meta: Dict


def _stable_hash(obj: Dict) -> str:
    """
    Deterministic hash for JSON-serializable dicts.
    Used only for identity bookkeeping, never for semantic querying.
    """
    blob = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:16]


class PersistentStore:
    """
    Append-only store for motif versions.

    This store intentionally does NOT:
    - expose search/query endpoints
    - evaluate constraints
    - compute satisfaction
    - allow mutation of stored versions

    Allowed operations:
    - create motif (initial version)
    - append version (new revision)
    - read specific version (by ID)
    - get lineage (by following parent pointers)
    """

    def __init__(self) -> None:
        # motif_id -> list of version_ids (append-only order)
        self._motif_versions: Dict[str, List[str]] = {}
        # version_id -> MotifVersion
        self._versions: Dict[str, MotifVersion] = {}

    # -----------------------------
    # Allowed API
    # -----------------------------

    def create_motif(self, motif_id: str, payload: Dict, *, meta: Optional[Dict] = None) -> MotifVersion:
        """
        Create a new motif with an initial version.
        """
        if motif_id in self._motif_versions:
            raise StoreInvariantViolation(f"Motif '{motif_id}' already exists.")

        meta = dict(meta or {})
        parent_version_id = None
        version_id = self._make_version_id(motif_id, payload, parent_version_id, meta)

        mv = MotifVersion(
            motif_id=motif_id,
            version_id=version_id,
            parent_version_id=parent_version_id,
            created_at_unix=time.time(),
            payload=_deepcopy_json(payload),
            meta=_deepcopy_json(meta),
        )
        self._versions[version_id] = mv
        self._motif_versions[motif_id] = [version_id]
        return mv

    def append_version(
        self,
        motif_id: str,
        payload: Dict,
        *,
        parent_version_id: Optional[str] = None,
        meta: Optional[Dict] = None,
    ) -> MotifVersion:
        """
        Append a new version to an existing motif.

        Requires correct parent_version_id (default: latest).
        Enforces append-only lineage (no branching in this minimal store).
        """
        if motif_id not in self._motif_versions:
            raise StoreInvariantViolation(f"Motif '{motif_id}' does not exist.")

        lineage = self._motif_versions[motif_id]
        latest = lineage[-1]

        if parent_version_id is None:
            parent_version_id = latest

        if parent_version_id != latest:
            # In the minimal store we forbid branching to keep identity simple.
            raise StoreInvariantViolation(
                f"Non-linear lineage forbidden in prototype. "
                f"Parent must be latest={latest}, got={parent_version_id}."
            )

        meta = dict(meta or {})
        version_id = self._make_version_id(motif_id, payload, parent_version_id, meta)

        if version_id in self._versions:
            raise StoreInvariantViolation(f"Version '{version_id}' already exists (hash collision?).")

        mv = MotifVersion(
            motif_id=motif_id,
            version_id=version_id,
            parent_version_id=parent_version_id,
            created_at_unix=time.time(),
            payload=_deepcopy_json(payload),
            meta=_deepcopy_json(meta),
        )
        self._versions[version_id] = mv
        self._motif_versions[motif_id].append(version_id)
        return mv

    def read_version(self, version_id: str) -> MotifVersion:
        """
        Read an immutable snapshot by version id.
        """
        if version_id not in self._versions:
            raise KeyError(f"Unknown version_id: {version_id}")
        return self._versions[version_id]

    def latest_version(self, motif_id: str) -> MotifVersion:
        """
        Get latest version snapshot for a motif.
        """
        if motif_id not in self._motif_versions:
            raise KeyError(f"Unknown motif_id: {motif_id}")
        return self._versions[self._motif_versions[motif_id][-1]]

    def lineage(self, motif_id: str) -> List[MotifVersion]:
        """
        Return full version lineage for motif_id in append order.
        """
        if motif_id not in self._motif_versions:
            raise KeyError(f"Unknown motif_id: {motif_id}")
        return [self._versions[vid] for vid in self._motif_versions[motif_id]]

    # -----------------------------
    # Forbidden "DB-like" API
    # -----------------------------

    def query(self, *args, **kwargs):
        raise NonQueryabilityViolation(
            "Query API is forbidden. Persistent structures are navigated/versioned, not queried/solved."
        )

    def search(self, *args, **kwargs):
        raise NonQueryabilityViolation(
            "Search API is forbidden. Persistent structures are not an information retrieval substrate."
        )

    def evaluate(self, *args, **kwargs):
        raise NonQueryabilityViolation(
            "Evaluate API is forbidden. Persistent structures cannot be satisfied/validated by inference."
        )

    # -----------------------------
    # Internal helpers
    # -----------------------------

    @staticmethod
    def _make_version_id(
        motif_id: str,
        payload: Dict,
        parent_version_id: Optional[str],
        meta: Dict,
    ) -> str:
        # Version identity is derived from (motif_id, parent, payload, meta).
        # This is lineage-aware and content-addressed, but not semantic.
        seed = {
            "motif_id": motif_id,
            "parent": parent_version_id,
            "payload": payload,
            "meta": meta,
        }
        return f"{motif_id}:{_stable_hash(seed)}"


def _deepcopy_json(obj):
    """
    Safe-ish deepcopy for JSON-like structures without importing copy (keeps intent explicit).
    """
    return json.loads(json.dumps(obj, ensure_ascii=False))


def minimal_motif_payload(*, tensions: Iterable[str], notes: Optional[str] = None) -> Dict:
    """
    Convenience helper to produce a tiny, semantically-neutral motif payload.

    A 'motif' is represented as:
    - tensions: a list of decision tensions the system must preserve (not solve)
    - relations: optional edges (purely structural, not executable)
    """
    return {
        "tensions": list(tensions),
        "relations": [],
        "notes": notes or "",
    }
