"""Universal Basic Income streaming primitives."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable

from .identity import IdentityRegistry
from .tokenomics import Ledger, MonetaryPolicy, Token


@dataclass
class Stream:
    identity: str
    amount_per_epoch: int
    last_epoch: int = -1


class UBIStreamScheduler:
    """Manages MSR-based income streams for verified identities."""

    def __init__(
        self,
        identity_registry: IdentityRegistry,
        ledger: Ledger,
        token: Token,
        policy: MonetaryPolicy,
    ) -> None:
        self._identity_registry = identity_registry
        self._ledger = ledger
        self._token = token
        self._policy = policy
        self._streams: Dict[str, Stream] = {}

    def refresh_streams(self) -> None:
        """Ensure every verified identity has a stream."""
        verified_ids = {identity.identifier for identity in self._identity_registry.verified_identities()}
        for identifier in verified_ids:
            self._streams.setdefault(
                identifier,
                Stream(identity=identifier, amount_per_epoch=self._policy.base_rate),
            )
        # Remove streams for unverified identities
        for identifier in list(self._streams):
            if identifier not in verified_ids:
                del self._streams[identifier]

    def distribute(self, epoch: int) -> Dict[str, int]:
        if epoch < 0:
            raise ValueError("epoch must be non-negative")
        self.refresh_streams()
        payouts: Dict[str, int] = {}
        for stream in self._streams.values():
            if stream.last_epoch == epoch:
                continue
            stream.amount_per_epoch = self._policy.issuance_for_epoch(epoch)
            self._ledger.credit(stream.identity, self._token.symbol, stream.amount_per_epoch)
            self._token.mint(stream.amount_per_epoch)
            stream.last_epoch = epoch
            payouts[stream.identity] = stream.amount_per_epoch
        return payouts

    def active_streams(self) -> Iterable[Stream]:
        return self._streams.values()
