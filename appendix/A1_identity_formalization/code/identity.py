# persistent-reasoning-architecture/appendix/A1_identity_formalization/code/identity.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional
import hashlib

from .canonicalization import canonicalize_payload


class IdentityError(ValueError):
    """Raised when an identity anchor cannot be created or validated."""


def _blake2b_256(data: bytes) -> str:
    # 32 bytes = 256-bit digest; stable, fast, and available in stdlib.
    h = hashlib.blake2b(data, digest_size=32)
    return h.hexdigest()


def canonical_fingerprint(
    *,
    kind: str,
    namespace: str,
    payload: Mapping[str, Any],
    scope: str = "global",
    version: str = "v1",
) -> str:
    """
    Compute a stable fingerprint from canonicalized payload + identity metadata.

    Notes:
    - This is NOT semantic equivalence.
    - This is an identity anchor for persistence + lineage tracking.
    - Any change to the canonicalized payload changes the fingerprint.
    """
    if not kind or not namespace:
        raise IdentityError("kind and namespace must be non-empty strings")

    canonical = canonicalize_payload(payload)
    material = {
        "version": version,
        "kind": kind,
        "namespace": namespace,
        "scope": scope,
        "payload": canonical,
    }
    # canonicalize again at the outer layer to guarantee stability
    outer = canonicalize_payload(material)
    return _blake2b_256(outer.encode("utf-8"))


@dataclass(frozen=True, slots=True)
class IdentityAnchor:
    """
    IdentityAnchor = minimal, collision-resistant marker for a persistent object.

    Design constraints:
    - Stable across runs (deterministic).
    - Independent from runtime memory addresses.
    - Safe to log and compare.
    - Not a "meaning" representation (no entailment semantics).

    Fields:
    - id: the fingerprint hex string
    - kind: object category (e.g., "motif", "invariant", "kau")
    - namespace: domain/tenant boundary for collision containment
    - scope: applicability scope (informational; included in fingerprint)
    - version: schema version of the anchor construction
    """
    id: str
    kind: str
    namespace: str
    scope: str = "global"
    version: str = "v1"

    @staticmethod
    def create(
        *,
        kind: str,
        namespace: str,
        payload: Mapping[str, Any],
        scope: str = "global",
        version: str = "v1",
    ) -> "IdentityAnchor":
        fp = canonical_fingerprint(
            kind=kind,
            namespace=namespace,
            payload=payload,
            scope=scope,
            version=version,
        )
        return IdentityAnchor(id=fp, kind=kind, namespace=namespace, scope=scope, version=version)

    def short(self, n: int = 10) -> str:
        return self.id[: max(4, n)]

    def validate(self) -> None:
        if not isinstance(self.id, str) or len(self.id) < 32:
            raise IdentityError("invalid id format")
        if not self.kind or not self.namespace:
            raise IdentityError("kind and namespace must be non-empty")
        if self.version != "v1":
            # Future versions must be explicitly supported.
            raise IdentityError(f"unsupported IdentityAnchor version: {self.version}")


def maybe_anchor_equal(a: Optional[IdentityAnchor], b: Optional[IdentityAnchor]) -> bool:
    """
    Safe equality helper when anchors might be None.
    """
    if a is None or b is None:
        return False
    return (a.id == b.id) and (a.kind == b.kind) and (a.namespace == b.namespace) and (a.scope == b.scope)
