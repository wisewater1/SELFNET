from selfnet.lottery import VRFLottery
from selfnet.tokenomics import Ledger, Token


def test_lottery_draw_awards_prize_and_is_replayable(monkeypatch):
    ledger = Ledger()
    token = Token(symbol="SELF")
    lottery = VRFLottery(ledger, token, prize_amount=100)

    # Use deterministic seed for testing
    monkeypatch.setattr(lottery, "_random_seed", lambda: "seed")
    participants = ["alice", "bob", "carol"]
    result = lottery.draw(participants, winner_count=2)
    assert result.seed == "seed"
    assert len(result.winners) == 2
    for winner in result.winners:
        assert ledger.balance(winner, "SELF") == 100
    assert token.total_supply == 200

    replay_result = lottery.replay(result.seed, participants, winner_count=2)
    assert replay_result.winners == result.winners
