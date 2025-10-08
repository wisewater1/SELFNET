"""Identity primitives used to model SELFNet proof-of-personhood."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Optional


@dataclass(frozen=True)
class Identity:
    """Simple representation of a verified human participant."""

    identifier: str
    attestations: frozenset[str] = field(default_factory=frozenset)

    def trusted_score(self, trusted_sources: set[str]) -> float:
        """Return a trust score based on overlap with trusted sources.

        Args:
            trusted_sources: Known good attestations (e.g. validators or peers).
        """

        if not self.attestations:
            return 0.0
        overlap = len(self.attestations & trusted_sources)
        return overlap / len(self.attestations)


class IdentityRegistry:
    """Registry managing verified identities and their attestations."""

    def __init__(self, minimum_trust: float = 0.51) -> None:
        self._minimum_trust = minimum_trust
        self._identities: Dict[str, Identity] = {}
        self._trusted_sources: set[str] = set()

    @property
    def minimum_trust(self) -> float:
        return self._minimum_trust

    def add_trusted_source(self, source_id: str) -> None:
        self._trusted_sources.add(source_id)

    def register_identity(
        self,
        identifier: str,
        attestations: Optional[Iterable[str]] = None,
    ) -> Identity:
        identity = Identity(identifier, frozenset(attestations or ()))
        self._identities[identifier] = identity
        return identity

    def get(self, identifier: str) -> Optional[Identity]:
        return self._identities.get(identifier)

    def is_verified(self, identifier: str) -> bool:
        identity = self.get(identifier)
        if not identity:
            return False
        if not identity.attestations:
            return False
        score = identity.trusted_score(self._trusted_sources)
        return score >= self._minimum_trust

    def verified_identities(self) -> Iterable[Identity]:
        for identity in self._identities.values():
            if self.is_verified(identity.identifier):
                yield identity

    def identities(self) -> Iterable[Identity]:
        """Iterate over all registered identities."""

        return self._identities.values()
