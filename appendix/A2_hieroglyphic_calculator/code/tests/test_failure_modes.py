# persistent-reasoning-architecture/appendix/A2_hieroglyphic_calculator/code/tests/test_failure_modes.py
"""
Failure mode tests for A2 boundary enforcement.

These tests focus on:
- rejecting solver-like transform ids
- rejecting invalid payload drift
- ensuring the checker blocks before commit
"""

from __future__ import annotations

import unittest

from src.checker import check_candidate
from src.state import expr_add, expr_const, expr_mul, InMemoryLineageStore
from src.transforms import NormalizeOrdering, apply_transform_to_candidate


class TestFailureModes(unittest.TestCase):
    def test_reject_solver_like_transform_id(self) -> None:
        store = InMemoryLineageStore()
        ns = "A2:test:solver_id"
        store.bootstrap(namespace=ns, scope="A2:arithmetic:int", payload=expr_add([expr_const(2), expr_const(2)]))
        head = store.head(ns)

        cand = apply_transform_to_candidate(
            transform=NormalizeOrdering(),
            scope=head.scope,
            payload=head.payload,
            parent_id=head.state_id,
        )
        # mutate id into a forbidden "eval/solve" marker
        cand["meta"]["transform_id"] = "solve_eval_all"
        chk = check_candidate(cand)
        self.assertFalse(chk.ok)
        self.assertTrue(any("FORBIDDEN_TRANSFORM_ID" in r for r in chk.reasons))

    def test_reject_negative_const_payload(self) -> None:
        store = InMemoryLineageStore()
        ns = "A2:test:neg"
        store.bootstrap(namespace=ns, scope="A2:arithmetic:int", payload=expr_add([expr_const(2), expr_const(2)]))
        head = store.head(ns)

        cand = {
            "scope": head.scope,
            "payload": expr_add([expr_const(2), expr_const(-1)]),
            "meta": {"parent_id": head.state_id, "transform_id": "manual_inject"},
        }
        chk = check_candidate(cand)
        self.assertFalse(chk.ok)
        self.assertTrue(any("NEGATIVE_CONST" in r for r in chk.reasons))

    def test_reject_solver_like_payload_collapse(self) -> None:
        # Collapsing structured expr into const is allowed by envelope,
        # but must be rejected if presented as "solve/eval" (wrong path).
        store = InMemoryLineageStore()
        ns = "A2:test:collapse"
        store.bootstrap(
            namespace=ns,
            scope="A2:arithmetic:int",
            payload=expr_mul([expr_add([expr_const(2), expr_const(2)]), expr_const(3)]),
        )
        head = store.head(ns)

        cand = {
            "scope": head.scope,
            "payload": expr_const(12),
            "meta": {"parent_id": head.state_id, "transform_id": "eval_everything"},
        }
        chk = check_candidate(cand)
        self.assertFalse(chk.ok)
        self.assertTrue(any("FORBIDDEN_TRANSFORM_ID" in r for r in chk.reasons))

    def test_checker_blocks_before_commit(self) -> None:
        store = InMemoryLineageStore()
        ns = "A2:test:block"
        store.bootstrap(namespace=ns, scope="A2:arithmetic:int", payload=expr_add([expr_const(1), expr_const(1)]))
        head = store.head(ns)

        bad = {
            "scope": head.scope,
            "payload": expr_add([expr_const(1), expr_const(-1)]),
            "meta": {"parent_id": head.state_id, "transform_id": "manual_inject"},
        }
        chk = check_candidate(bad)
        self.assertFalse(chk.ok)

        # We deliberately do NOT commit if checker fails.
        # Simulate correct orchestrator behavior.
        if chk.ok:  # pragma: no cover
            store.commit(ns, bad)

        # ensure head didn't change
        head2 = store.head(ns)
        self.assertEqual(head.state_id, head2.state_id)
        self.assertEqual(head.payload, head2.payload)


if __name__ == "__main__":
    unittest.main()