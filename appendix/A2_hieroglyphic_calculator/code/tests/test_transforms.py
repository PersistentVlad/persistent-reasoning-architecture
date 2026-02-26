# persistent-reasoning-architecture/appendix/A2_hieroglyphic_calculator/code/tests/test_transforms.py
"""
Unit tests for allowed transforms.

Important: transforms are structural normalizations.
They must not evaluate expressions into answers.
"""

from __future__ import annotations

import unittest

from src.invariants import envelope_ok
from src.state import expr_add, expr_const, expr_mul
from src.transforms import (
    FlattenAssociative,
    NormalizeOrdering,
    apply_transform,
)


class TestTransforms(unittest.TestCase):
    def test_flatten_add(self) -> None:
        # (2 + (3 + 4)) + 1  ->  add[2,3,4,1] (ordering not required here)
        payload = expr_add([expr_add([expr_const(2), expr_add([expr_const(3), expr_const(4)])]), expr_const(1)])
        t = FlattenAssociative("add")
        out = apply_transform(t, payload)
        self.assertTrue(envelope_ok(out))
        self.assertEqual(out["type"], "add")
        # ensure it's flatter than before (no immediate child add nodes)
        self.assertTrue(all(a.get("type") != "add" for a in out["args"]))

    def test_flatten_mul(self) -> None:
        payload = expr_mul([expr_const(2), expr_mul([expr_const(3), expr_const(4)])])
        t = FlattenAssociative("mul")
        out = apply_transform(t, payload)
        self.assertTrue(envelope_ok(out))
        self.assertEqual(out["type"], "mul")
        self.assertTrue(all(a.get("type") != "mul" for a in out["args"]))

    def test_normalize_ordering_is_deterministic(self) -> None:
        # Same multiset of args should normalize to same order.
        a = expr_add([expr_const(3), expr_const(1), expr_const(2)])
        b = expr_add([expr_const(2), expr_const(3), expr_const(1)])
        t = NormalizeOrdering()

        out_a = apply_transform(t, a)
        out_b = apply_transform(t, b)

        self.assertTrue(envelope_ok(out_a))
        self.assertTrue(envelope_ok(out_b))
        self.assertEqual(out_a, out_b)

    def test_transforms_do_not_evaluate(self) -> None:
        # (2 + 2) * 3 should not become const(12) under allowed transforms.
        payload = expr_mul([expr_add([expr_const(2), expr_const(2)]), expr_const(3)])
        out = apply_transform(NormalizeOrdering(), payload)
        out = apply_transform(FlattenAssociative("add"), out)  # might not change, but should not evaluate
        self.assertNotEqual(out.get("type"), "const")  # must remain structured
        self.assertTrue(envelope_ok(out))


if __name__ == "__main__":
    unittest.main()