# persistent-reasoning-architecture/appendix/A2_hieroglyphic_calculator/code/src/state.py
"""
State model for Appendix A2 — Hieroglyphic Calculator.

Design goals:
- Small, explicit, deterministic state container
- No hidden global state, no learning, no querying interface
- Friendly to append-only lineage (parent pointer + transform id)

Important:
- This state is NOT an "answer".
- It is a committed snapshot of a transformation step that survived invariants.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional


@dataclass(frozen=True)
class PRState:
    """
    A minimal immutable state record.

    Fields:
    - state_id: stable handle assigned by the lineage store at commit time
    - scope: explicit boundary marker (e.g., "A2:arithmetic:int")
    - payload: the symbolic payload (expression tree / simplified dict)
    - meta: minimal provenance needed for audit / replay (parent_id, transform_id, note)
    """
    state_id: str
    scope: str
    payload: Mapping[str, Any]
    meta: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "state_id": self.state_id,
            "scope": self.scope,
            "payload": dict(self.payload),
            "meta": dict(self.meta),
        }


def make_candidate_state(
    *,
    scope: str,
    payload: Mapping[str, Any],
    parent_id: str,
    transform_id: str,
    note: str = "",
) -> Dict[str, Any]:
    """
    Build a *candidate* state dict (without state_id).
    This is what invariants validate before commit.

    The lineage store assigns the final state_id.
    """
    meta: Dict[str, Any] = {"parent_id": parent_id, "transform_id": transform_id}
    if note:
        meta["note"] = note
    return {
        "scope": scope,
        "payload": dict(payload),
        "meta": meta,
    }


# ----------------------------
# Helpers expected by demo_runs.py
# ----------------------------

def expr_const(value: int) -> Dict[str, Any]:
    return {"kind": "const", "value": int(value)}

def expr_add(args: List[Mapping[str, Any]]) -> Dict[str, Any]:
    return {"kind": "add", "args": [dict(a) for a in args]}

def expr_mul(args: List[Mapping[str, Any]]) -> Dict[str, Any]:
    return {"kind": "mul", "args": [dict(a) for a in args]}


# ----------------------------
# In-Memory Store (for demo)
# ----------------------------

class InMemoryLineageStore:
    """
    Simple in-memory implementation of LineageStore for demos.
    """
    def __init__(self) -> None:
        self._states: Dict[str, PRState] = {}
        self._heads: Dict[str, str] = {}

    def get(self, state_id: str) -> PRState:
        if state_id not in self._states:
            raise KeyError(f"State not found: {state_id}")
        return self._states[state_id]

    def head(self, namespace: str) -> PRState:
        sid = self._heads.get(namespace)
        if not sid:
            raise KeyError(f"No head for namespace: {namespace}")
        return self.get(sid)

    def commit(self, namespace: str, candidate: Mapping[str, Any]) -> PRState:
        # Generate a simple ID
        idx = len(self._states) + 1
        state_id = f"state_{idx:03d}"
        
        st = PRState(
            state_id=state_id,
            scope=candidate["scope"],
            payload=candidate["payload"],
            meta=candidate["meta"],
        )
        self._states[state_id] = st
        self._heads[namespace] = state_id
        return st

    def bootstrap(self, namespace: str, scope: str, payload: Mapping[str, Any], meta: Mapping[str, Any]) -> None:
        """Helper to seed the store."""
        cand = {
            "scope": scope,
            "payload": payload,
            "meta": meta
        }
        self.commit(namespace, cand)