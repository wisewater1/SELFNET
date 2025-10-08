from selfnet.governance import GovernanceSystem, Vote
from selfnet.identity import IdentityRegistry
from selfnet.tokenomics import Ledger


def setup_system():
    ledger = Ledger()
    registry = IdentityRegistry(minimum_trust=0.5)
    registry.add_trusted_source("validator:1")
    registry.register_identity("alice", ["validator:1", "bob"])
    registry.register_identity("bob", ["validator:1"])
    governance = GovernanceSystem(ledger, "SELF", registry)
    return ledger, registry, governance


def test_proposal_passes_with_dual_majorities():
    ledger, registry, governance = setup_system()
    proposal = governance.submit_proposal("upgrade", "Upgrade protocol", quorum=100, threshold=0.6)
    ledger.credit("validator", "SELF", 120)
    governance.cast_stake_vote("upgrade", "validator", Vote.YES)
    governance.cast_citizen_vote("upgrade", "alice", Vote.YES)
    governance.cast_citizen_vote("upgrade", "bob", Vote.YES)
    assert governance.resolve("upgrade")


def test_proposal_fails_without_citizen_support():
    ledger, registry, governance = setup_system()
    proposal = governance.submit_proposal("treasury", "Allocate treasury", quorum=80, threshold=0.5)
    ledger.credit("validator", "SELF", 100)
    governance.cast_stake_vote("treasury", "validator", Vote.YES)
    # No citizen votes are cast -> fails due to citizen chamber
    assert not governance.resolve("treasury")
