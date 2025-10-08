"""Token and ledger primitives for SELFNet simulations."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class Token:
    """Simple fungible token model with a mutable total supply."""

    symbol: str
    decimals: int = 18
    total_supply: int = 0

    def mint(self, amount: int) -> None:
        if amount < 0:
            raise ValueError("cannot mint negative amount")
        self.total_supply += amount

    def burn(self, amount: int) -> None:
        if amount < 0:
            raise ValueError("cannot burn negative amount")
        if amount > self.total_supply:
            raise ValueError("burn exceeds total supply")
        self.total_supply -= amount


class Ledger:
    """Account-based ledger supporting multiple tokens."""

    def __init__(self) -> None:
        self._balances: Dict[str, Dict[str, int]] = {}

    def _ensure_account(self, account: str) -> Dict[str, int]:
        return self._balances.setdefault(account, {})

    def balance(self, account: str, symbol: str) -> int:
        return self._balances.get(account, {}).get(symbol, 0)

    def credit(self, account: str, symbol: str, amount: int) -> None:
        if amount < 0:
            raise ValueError("cannot credit negative amount")
        account_balances = self._ensure_account(account)
        account_balances[symbol] = account_balances.get(symbol, 0) + amount

    def debit(self, account: str, symbol: str, amount: int) -> None:
        if amount < 0:
            raise ValueError("cannot debit negative amount")
        account_balances = self._ensure_account(account)
        previous = account_balances.get(symbol, 0)
        if amount > previous:
            raise ValueError("insufficient balance")
        account_balances[symbol] = previous - amount

    def transfer(self, sender: str, receiver: str, symbol: str, amount: int) -> None:
        self.debit(sender, symbol, amount)
        self.credit(receiver, symbol, amount)

    def snapshot(self) -> Dict[str, Dict[str, int]]:
        """Return a copy of all balances for display purposes."""

        return {account: balances.copy() for account, balances in self._balances.items()}


@dataclass
class MonetaryPolicy:
    """Represents the Monetary Supply Rate (MSR) used for UBI streams."""

    base_rate: int
    acceleration: int = 0
    cap: int | None = None

    def issuance_for_epoch(self, epoch: int) -> int:
        if epoch < 0:
            raise ValueError("epoch must be non-negative")
        issuance = self.base_rate + self.acceleration * epoch
        if self.cap is not None:
            issuance = min(issuance, self.cap)
        return max(issuance, 0)
