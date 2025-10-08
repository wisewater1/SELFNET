from selfnet.identity import IdentityRegistry
from selfnet.tokenomics import Ledger, MonetaryPolicy, Token
from selfnet.ubi import UBIStreamScheduler


def setup_environment(minimum_trust=0.5):
    registry = IdentityRegistry(minimum_trust=minimum_trust)
    registry.add_trusted_source("validator:1")
    ledger = Ledger()
    token = Token(symbol="CPT")
    policy = MonetaryPolicy(base_rate=10, acceleration=1, cap=20)
    scheduler = UBIStreamScheduler(registry, ledger, token, policy)
    return registry, ledger, token, scheduler


def test_scheduler_distributes_per_epoch():
    registry, ledger, token, scheduler = setup_environment()
    registry.register_identity("alice", ["validator:1"])
    payouts = scheduler.distribute(epoch=0)
    assert payouts == {"alice": 10}
    assert ledger.balance("alice", "CPT") == 10
    assert token.total_supply == 10


def test_scheduler_respects_cap():
    registry, ledger, token, scheduler = setup_environment()
    registry.register_identity("alice", ["validator:1"])
    registry.register_identity("bob", ["validator:1"])
    payouts_epoch_5 = scheduler.distribute(epoch=5)
    assert payouts_epoch_5 == {"alice": 15, "bob": 15}
    payouts_epoch_15 = scheduler.distribute(epoch=15)
    assert payouts_epoch_15 == {"alice": 20, "bob": 20}
    assert token.total_supply == 30 + 40
