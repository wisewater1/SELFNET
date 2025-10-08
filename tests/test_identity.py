from selfnet.identity import IdentityRegistry


def test_identity_verification_with_trusted_attestations():
    registry = IdentityRegistry(minimum_trust=0.5)
    registry.add_trusted_source("validator:1")
    registry.register_identity("alice", ["validator:1", "bob"])
    assert registry.is_verified("alice")


def test_identity_rejects_untrusted_identity():
    registry = IdentityRegistry(minimum_trust=0.75)
    registry.add_trusted_source("validator:1")
    registry.register_identity("bob", ["validator:1", "carol", "dave"])
    assert not registry.is_verified("bob")
