"""VRF inspired lottery primitive."""
from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from typing import List, Sequence

from .tokenomics import Ledger, Token


@dataclass
class LotteryResult:
    seed: str
    winners: List[str]
    prize: int


class VRFLottery:
    """Draws lottery winners using deterministic randomness derived from a seed."""

    def __init__(
        self,
        ledger: Ledger,
        prize_token: Token,
        prize_amount: int,
    ) -> None:
        if prize_amount <= 0:
            raise ValueError("prize_amount must be positive")
        self._ledger = ledger
        self._token = prize_token
        self._prize_amount = prize_amount

    def _random_seed(self) -> str:
        return secrets.token_hex(32)

    def _hash(self, value: str) -> bytes:
        return hashlib.sha256(value.encode("utf-8")).digest()

    def draw(self, participants: Sequence[str], winner_count: int = 1) -> LotteryResult:
        if winner_count <= 0:
            raise ValueError("winner_count must be positive")
        if not participants:
            raise ValueError("no participants provided")
        seed = self._random_seed()
        winners = self._select_winners(seed, participants, winner_count)
        for winner in winners:
            self._ledger.credit(winner, self._token.symbol, self._prize_amount)
            self._token.mint(self._prize_amount)
        return LotteryResult(seed=seed, winners=winners, prize=self._prize_amount)

    def _select_winners(
        self,
        seed: str,
        participants: Sequence[str],
        winner_count: int,
    ) -> List[str]:
        winners: List[str] = []
        cursor = seed
        available = list(participants)
        while available and len(winners) < winner_count:
            hashed = self._hash(cursor)
            index = int.from_bytes(hashed, "big") % len(available)
            winners.append(available.pop(index))
            cursor = f"{cursor}:{index}"
        return winners

    def replay(self, seed: str, participants: Sequence[str], winner_count: int = 1) -> LotteryResult:
        winners = self._select_winners(seed, participants, winner_count)
        return LotteryResult(seed=seed, winners=winners, prize=self._prize_amount)
