"""Two-house governance simulation for SELFNet."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, Iterable

from .identity import IdentityRegistry
from .tokenomics import Ledger


class Vote(Enum):
    ABSTAIN = auto()
    YES = auto()
    NO = auto()


@dataclass
class Proposal:
    identifier: str
    description: str
    quorum: int
    threshold: float
    votes: Dict[str, Vote] = field(default_factory=dict)
    citizen_votes: Dict[str, Vote] = field(default_factory=dict)

    def tally(self, voting_power: Dict[str, int], citizen_identities: Iterable[str]) -> bool:
        yes_power = sum(
            voting_power.get(voter, 0)
            for voter, vote in self.votes.items()
            if vote == Vote.YES
        )
        no_power = sum(
            voting_power.get(voter, 0)
            for voter, vote in self.votes.items()
            if vote == Vote.NO
        )
        total_power = yes_power + no_power
        if total_power < self.quorum:
            return False
        if total_power == 0:
            return False
        stake_passed = yes_power / total_power >= self.threshold

        citizen_votes = [self.citizen_votes.get(cid, Vote.ABSTAIN) for cid in citizen_identities]
        citizen_yes = citizen_votes.count(Vote.YES)
        citizen_no = citizen_votes.count(Vote.NO)
        citizen_total = citizen_yes + citizen_no
        if citizen_total == 0:
            citizen_passed = False
        else:
            citizen_passed = citizen_yes / citizen_total >= self.threshold
        return stake_passed and citizen_passed


class GovernanceSystem:
    """Combines stake-weighted and identity-weighted voting."""

    def __init__(self, ledger: Ledger, stake_token_symbol: str, registry: IdentityRegistry) -> None:
        self._ledger = ledger
        self._stake_token_symbol = stake_token_symbol
        self._registry = registry
        self._proposals: Dict[str, Proposal] = {}

    def submit_proposal(
        self,
        identifier: str,
        description: str,
        quorum: int,
        threshold: float = 0.5,
    ) -> Proposal:
        if identifier in self._proposals:
            raise ValueError("proposal already exists")
        proposal = Proposal(identifier, description, quorum, threshold)
        self._proposals[identifier] = proposal
        return proposal

    def proposals(self) -> Iterable[Proposal]:
        return self._proposals.values()

    def cast_stake_vote(self, proposal_id: str, voter: str, vote: Vote) -> None:
        proposal = self._require_proposal(proposal_id)
        proposal.votes[voter] = vote

    def cast_citizen_vote(self, proposal_id: str, identity: str, vote: Vote) -> None:
        if not self._registry.is_verified(identity):
            raise ValueError("identity is not verified")
        proposal = self._require_proposal(proposal_id)
        proposal.citizen_votes[identity] = vote

    def resolve(self, proposal_id: str) -> bool:
        proposal = self._require_proposal(proposal_id)
        voting_power = {
            account: self._ledger.balance(account, self._stake_token_symbol)
            for account in proposal.votes
        }
        citizen_identities = [identity.identifier for identity in self._registry.verified_identities()]
        return proposal.tally(voting_power, citizen_identities)

    def _require_proposal(self, proposal_id: str) -> Proposal:
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            raise KeyError(f"unknown proposal {proposal_id}")
        return proposal
