# persistent-reasoning-architecture/appendix/A2_hieroglyphic_calculator/code/tests/test_invariants.py
"""
Unit tests for A2 invariants.

These tests intentionally verify only the invariant envelope, not "correctness" of
arithmetic evaluation. A2 is an academic boundary case: it forbids drift paths and
solver-like collapse.
"""

from __future__ import annotations

import unittest

from src.invariants import (
    InvariantViolation,
    check_envelope,
    envelope_ok,
)
from src.state import (
    expr_add,
    expr_const,
    expr_mul,
)


class TestInvariantEnvelope(unittest.TestCase):
    def test_ok_small_expression(self) -> None:
        payload = expr_add([expr_const(2), expr_mul([expr_const(3), expr_const(4)])])
        violations = check_envelope(payload)
        self.assertEqual(violations, [])

    def test_reject_negative_constant(self) -> None:
        payload = expr_add([expr_const(2), expr_const(-1)])
        violations = check_envelope(payload)
        self.assertTrue(any(v.code == "NEGATIVE_CONST" for v in violations))

    def test_reject_non_int_constant(self) -> None:
        payload = {"type": "const", "value": "2"}  # wrong type
        violations = check_envelope(payload)
        self.assertTrue(any(v.code == "NON_INT_CONST" for v in violations))

    def test_reject_unknown_node_type(self) -> None:
        payload = {"type": "pow", "base": expr_const(2), "exp": expr_const(3)}
        violations = check_envelope(payload)
        self.assertTrue(any(v.code == "UNKNOWN_NODE_TYPE" for v in violations))

    def test_reject_missing_fields(self) -> None:
        payload = {"type": "add"}  # missing args
        violations = check_envelope(payload)
        self.assertTrue(any(v.code == "MALFORMED_NODE" for v in violations))

    def test_depth_limit(self) -> None:
        # Build a deep right-nested add chain to exceed typical depth.
        x = expr_const(1)
        for _ in range(200):
            x = expr_add([x, expr_const(1)])
        violations = check_envelope(x)
        self.assertTrue(any(v.code == "DEPTH_LIMIT" for v in violations))

    def test_node_limit(self) -> None:
        # Build a wide add with many constants to exceed node count limit.
        payload = expr_add([expr_const(1) for _ in range(5000)])
        violations = check_envelope(payload)
        self.assertTrue(any(v.code == "NODE_LIMIT" for v in violations))


if __name__ == "__main__":
    unittest.main()