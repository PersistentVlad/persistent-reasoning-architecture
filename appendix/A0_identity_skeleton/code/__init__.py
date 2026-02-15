# Copyright (c) 2026 Vladislav Bliznyukov
# Licensed under the MIT License.

"""
__init__.py

Minimal, constraint-first implementation scaffold for the Persistent Reasoning
prototype.

This package is intentionally small and intentionally underpowered.
It exists to demonstrate executable architectural boundaries, not capability.
"""

__all__ = [
    "persistent_store",
    "write_barrier",
    "proposal_engine",
    "commit_gate",
    "inference_stub",
    "run_minimal_loop",
]
