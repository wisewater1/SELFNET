"""WSGI application providing an interactive SELFNet simulation console."""
from __future__ import annotations

from dataclasses import dataclass, field
from html import escape
from pathlib import Path
from typing import Dict, Iterable, List, Tuple
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server
from wsgiref.util import setup_testing_defaults

from ..governance import GovernanceSystem, Vote
from ..identity import IdentityRegistry
from ..lottery import LotteryResult, VRFLottery
from ..tokenomics import Ledger, MonetaryPolicy, Token
from ..ubi import UBIStreamScheduler

STATIC_DIR = Path(__file__).with_suffix("").parent / "static"
STYLE_PATH = STATIC_DIR / "style.css"


@dataclass
class AppState:
    """Holds long-lived instances that back the interactive UI."""

    registry: IdentityRegistry = field(default_factory=IdentityRegistry)
    ledger: Ledger = field(default_factory=Ledger)
    token: Token = field(default_factory=lambda: Token(symbol="SELF"))
    policy: MonetaryPolicy = field(default_factory=lambda: MonetaryPolicy(base_rate=100))
    ubi: UBIStreamScheduler | None = None
    lottery: VRFLottery | None = None
    governance: GovernanceSystem | None = None
    last_epoch: int | None = None
    last_payouts: Dict[str, int] = field(default_factory=dict)
    last_lottery: LotteryResult | None = None
    flashes: List[Tuple[str, str]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.ubi is None:
            self.ubi = UBIStreamScheduler(self.registry, self.ledger, self.token, self.policy)
        if self.lottery is None:
            self.lottery = VRFLottery(self.ledger, self.token, prize_amount=250)
        if self.governance is None:
            self.governance = GovernanceSystem(self.ledger, self.token.symbol, self.registry)

    def balances(self) -> List[Tuple[str, Dict[str, int]]]:
        snapshot = self.ledger.snapshot()
        return sorted(snapshot.items())

    def verified_identities(self) -> List[str]:
        return sorted(identity.identifier for identity in self.registry.verified_identities())

    def all_identities(self) -> List[Tuple[str, Iterable[str], bool]]:
        entries: List[Tuple[str, Iterable[str], bool]] = []
        for identity in sorted(self.registry.identities(), key=lambda item: item.identifier):
            entries.append(
                (
                    identity.identifier,
                    sorted(identity.attestations),
                    self.registry.is_verified(identity.identifier),
                )
            )
        return entries

    def active_streams(self) -> List[Tuple[str, int, int]]:
        if self.ubi is None:
            return []
        return [
            (stream.identity, stream.amount_per_epoch, stream.last_epoch)
            for stream in self.ubi.active_streams()
        ]

    def proposals(self) -> List[Tuple[str, str, str]]:
        if self.governance is None:
            return []
        results: List[Tuple[str, str, str]] = []
        for proposal in self.governance.proposals():
            passed = self.governance.resolve(proposal.identifier)
            status = "Passed" if passed else "Pending / Failed"
            results.append((proposal.identifier, proposal.description, status))
        return results

    def flash(self, category: str, message: str) -> None:
        self.flashes.append((category, message))

    def consume_flashes(self) -> List[Tuple[str, str]]:
        flashes = list(self.flashes)
        self.flashes.clear()
        return flashes


def _read_body(environ: Dict[str, str]) -> Dict[str, str]:
    try:
        length = int(environ.get("CONTENT_LENGTH") or 0)
    except (TypeError, ValueError):
        length = 0
    data = environ.get("wsgi.input")
    if data is None:
        raw = b""
    else:
        raw = data.read(length)  # type: ignore[arg-type]
    parsed = parse_qs(raw.decode("utf-8"))
    return {key: values[-1] if values else "" for key, values in parsed.items()}


def _redirect(location: str) -> Tuple[str, List[Tuple[str, str]], bytes]:
    headers = [("Location", location)]
    return "303 See Other", headers, b""


def _serve_static(path: Path) -> Tuple[str, List[Tuple[str, str]], bytes]:
    if not path.exists():
        return "404 Not Found", [("Content-Type", "text/plain")], b"Not Found"
    body = path.read_bytes()
    headers = [("Content-Type", "text/css"), ("Content-Length", str(len(body)))]
    return "200 OK", headers, body


def _render_index(state: AppState) -> str:
    flashes = state.consume_flashes()
    html: List[str] = [
        "<!doctype html>",
        '<html lang="en">',
        "  <head>",
        '    <meta charset="utf-8" />',
        '    <meta name="viewport" content="width=device-width, initial-scale=1" />',
        "    <title>SELFNet Console</title>",
        "    <link rel=\"stylesheet\" href=\"/static/style.css\" />",
        "  </head>",
        "  <body>",
        "    <header>",
        "      <h1>SELFNet Simulation Console</h1>",
        "      <p>Interact with identity, UBI, lottery, and governance modules.</p>",
        "    </header>",
        "    <main>",
    ]
    if flashes:
        html.append("      <section>")
        for category, message in flashes:
            html.append(
                f"        <div class=\"flash {escape(category)}\">{escape(message)}</div>"
            )
        html.append("      </section>")

    html.append("      <section class=\"grid-two\">")
    html.append("        <div>")
    html.append("          <h2>Network Snapshot</h2>")
    html.append(f"          <p>Total SELF supply: <strong>{state.token.total_supply}</strong></p>")
    if state.last_epoch is not None:
        html.append(f"          <p>Last UBI epoch: <strong>{state.last_epoch}</strong></p>")
    if state.last_payouts:
        html.append("          <h3>Last Payouts</h3>")
        html.append("          <ul>")
        for identity, amount in state.last_payouts.items():
            html.append(f"            <li>{escape(identity)} received {amount} SELF</li>")
        html.append("          </ul>")
    if state.last_lottery:
        winners = ", ".join(escape(winner) for winner in state.last_lottery.winners)
        html.append("          <h3>Last Lottery</h3>")
        html.append(
            "          <p>Seed "
            + f"{escape(state.last_lottery.seed)} distributed "
            + f"<strong>{state.last_lottery.prize}</strong> SELF to {winners}</p>"
        )
    html.append("        </div>")

    html.append("        <div>")
    html.append("          <h2>Balances</h2>")
    balances = state.balances()
    if balances:
        html.append("          <table class=\"table\">")
        html.append("            <thead><tr><th>Account</th><th>SELF</th></tr></thead>")
        html.append("            <tbody>")
        for account, tokens in balances:
            html.append(
                f"              <tr><td>{escape(account)}</td><td>{tokens.get(state.token.symbol, 0)}</td></tr>"
            )
        html.append("            </tbody></table>")
    else:
        html.append("          <p>No balances yet.</p>")
    html.append("        </div>")
    html.append("      </section>")

    identities = state.all_identities()
    html.append("      <section class=\"grid-two\">")
    html.append("        <div>")
    html.append("          <h2>Identity Registry</h2>")
    if identities:
        html.append("          <table class=\"table\">")
        html.append("            <thead><tr><th>Identity</th><th>Attestations</th><th>Status</th></tr></thead>")
        html.append("            <tbody>")
        for identifier, attestations, verified in identities:
            status = "Verified" if verified else "Pending"
            att_text = ", ".join(attestations) if attestations else "—"
            html.append(
                f"              <tr><td>{escape(identifier)}</td><td>{escape(att_text)}</td><td>{status}</td></tr>"
            )
        html.append("            </tbody></table>")
    else:
        html.append("          <p>No identities registered yet.</p>")
    html.append("        </div>")

    html.append("        <div>")
    html.append("          <h2>Manage Identities</h2>")
    html.append(
        "          <form method=\"post\" action=\"/add-trusted-source\">"
        "<h3>Add Trusted Source</h3>"
        "<label for=\"source_id\">Trusted entity identifier</label>"
        "<input id=\"source_id\" name=\"source_id\" placeholder=\"validator-1\" required />"
        "<button type=\"submit\">Add trusted source</button>"
        "</form>"
    )
    html.append(
        "          <form method=\"post\" action=\"/register-identity\">"
        "<h3>Register Identity</h3>"
        "<label for=\"identifier\">Identity identifier</label>"
        "<input id=\"identifier\" name=\"identifier\" placeholder=\"alice\" required />"
        "<label for=\"attestations\">Attestations (comma or newline separated)</label>"
        "<textarea id=\"attestations\" name=\"attestations\" rows=\"3\" placeholder=\"validator-1, validator-2\"></textarea>"
        "<button type=\"submit\">Register identity</button>"
        "<small>Identities become verified when a majority of attestations are trusted.</small>"
        "</form>"
    )
    html.append("        </div>")
    html.append("      </section>")

    streams = state.active_streams()
    html.append("      <section class=\"grid-two\">")
    html.append("        <div>")
    html.append("          <h2>UBI Streams</h2>")
    if streams:
        html.append("          <table class=\"table\">")
        html.append("            <thead><tr><th>Identity</th><th>Amount / Epoch</th><th>Last Epoch</th></tr></thead>")
        html.append("            <tbody>")
        for identity, amount, last_epoch in streams:
            last_value = last_epoch if last_epoch != -1 else "—"
            html.append(
                f"              <tr><td>{escape(identity)}</td><td>{amount}</td><td>{last_value}</td></tr>"
            )
        html.append("            </tbody></table>")
    else:
        html.append("          <p>No active streams. Verify identities to mint UBI.</p>")
    html.append("        </div>")

    html.append("        <div>")
    html.append("          <h2>Trigger UBI Distribution</h2>")
    html.append(
        "          <form method=\"post\" action=\"/run-ubi\">"
        "<label for=\"epoch\">Epoch number</label>"
        "<input id=\"epoch\" name=\"epoch\" type=\"number\" min=\"0\" value=\"0\" required />"
        "<button type=\"submit\">Distribute UBI</button>"
        "</form>"
    )
    html.append(
        "          <h2 style=\"margin-top:1.5rem;\">Allocate Stake</h2>"
        "<form method=\"post\" action=\"/allocate-stake\">"
        "<label for=\"stake-account\">Account</label>"
        "<input id=\"stake-account\" name=\"account\" placeholder=\"validator-1\" required />"
        "<label for=\"stake-amount\">SELF amount</label>"
        "<input id=\"stake-amount\" name=\"amount\" type=\"number\" min=\"1\" value=\"100\" required />"
        "<button type=\"submit\">Mint stake</button>"
        "</form>"
    )
    html.append("        </div>")
    html.append("      </section>")

    proposals = state.proposals()
    html.append("      <section class=\"grid-two\">")
    html.append("        <div>")
    html.append("          <h2>VRF Lottery</h2>")
    html.append(
        "          <form method=\"post\" action=\"/draw-lottery\">"
        "<label for=\"participants\">Participants (comma or newline separated)</label>"
        "<textarea id=\"participants\" name=\"participants\" rows=\"3\" placeholder=\"alice, bob, carol\"></textarea>"
        "<label for=\"winner_count\">Number of winners</label>"
        "<input id=\"winner_count\" name=\"winner_count\" type=\"number\" min=\"1\" value=\"1\" />"
        "<button type=\"submit\">Draw lottery</button>"
        "</form>"
    )
    html.append("        </div>")

    html.append("        <div>")
    html.append("          <h2>Governance</h2>")
    html.append("          <h3>Active Proposals</h3>")
    if proposals:
        html.append("          <table class=\"table\">")
        html.append("            <thead><tr><th>ID</th><th>Description</th><th>Status</th></tr></thead>")
        html.append("            <tbody>")
        for identifier, description, status in proposals:
            html.append(
                f"              <tr><td>{escape(identifier)}</td><td>{escape(description)}</td><td>{status}</td></tr>"
            )
        html.append("            </tbody></table>")
    else:
        html.append("          <p>No proposals submitted.</p>")
    html.append(
        "          <form method=\"post\" action=\"/submit-proposal\">"
        "<h3>Submit Proposal</h3>"
        "<label for=\"proposal-id\">Proposal ID</label>"
        "<input id=\"proposal-id\" name=\"proposal_id\" placeholder=\"proposal-1\" required />"
        "<label for=\"proposal-description\">Description</label>"
        "<textarea id=\"proposal-description\" name=\"description\" rows=\"3\"></textarea>"
        "<label for=\"proposal-quorum\">Stake quorum</label>"
        "<input id=\"proposal-quorum\" name=\"quorum\" type=\"number\" min=\"0\" value=\"100\" />"
        "<label for=\"proposal-threshold\">Threshold (0-1)</label>"
        "<input id=\"proposal-threshold\" name=\"threshold\" type=\"number\" min=\"0\" max=\"1\" step=\"0.05\" value=\"0.5\" />"
        "<button type=\"submit\">Create proposal</button>"
        "</form>"
    )
    html.append("        </div>")
    html.append("      </section>")

    html.append("      <section class=\"grid-two\">")
    html.append("        <div>")
    html.append("          <h2>Stake Chamber Vote</h2>")
    html.append(
        "          <form method=\"post\" action=\"/stake-vote\">"
        "<label for=\"stake-proposal\">Proposal ID</label>"
        "<input id=\"stake-proposal\" name=\"proposal_id\" required />"
        "<label for=\"stake-voter\">Stake account</label>"
        "<input id=\"stake-voter\" name=\"account\" placeholder=\"validator-1\" required />"
        "<label for=\"stake-choice\">Vote</label>"
        "<select id=\"stake-choice\" name=\"vote\">"
        "<option value=\"yes\">Yes</option>"
        "<option value=\"no\">No</option>"
        "<option value=\"abstain\">Abstain</option>"
        "</select>"
        "<button type=\"submit\">Record stake vote</button>"
        "</form>"
    )
    html.append("        </div>")

    html.append("        <div>")
    html.append("          <h2>Citizen Chamber Vote</h2>")
    html.append(
        "          <form method=\"post\" action=\"/citizen-vote\">"
        "<label for=\"citizen-proposal\">Proposal ID</label>"
        "<input id=\"citizen-proposal\" name=\"proposal_id\" required />"
        "<label for=\"citizen-identity\">Verified identity</label>"
        "<input id=\"citizen-identity\" name=\"identity\" placeholder=\"alice\" required />"
        "<label for=\"citizen-choice\">Vote</label>"
        "<select id=\"citizen-choice\" name=\"vote\">"
        "<option value=\"yes\">Yes</option>"
        "<option value=\"no\">No</option>"
        "<option value=\"abstain\">Abstain</option>"
        "</select>"
        "<button type=\"submit\">Record citizen vote</button>"
        "</form>"
    )
    html.append("        </div>")
    html.append("      </section>")

    html.append("    </main>")
    html.append("  </body>")
    html.append("</html>")
    return "\n".join(html)


def _parse_vote(value: str) -> Vote:
    mapping = {"yes": Vote.YES, "no": Vote.NO, "abstain": Vote.ABSTAIN}
    vote = mapping.get(value.lower())
    if vote is None:
        raise ValueError("Unknown vote option")
    return vote


def create_app(state: AppState | None = None):
    """Return a WSGI application for the SELFNet console."""

    app_state = state or AppState()

    def app(environ, start_response):  # type: ignore[no-untyped-def]
        setup_testing_defaults(environ)
        method = environ["REQUEST_METHOD"].upper()
        path = environ.get("PATH_INFO", "/")

        if method == "GET" and path == "/":
            body = _render_index(app_state).encode("utf-8")
            headers = [
                ("Content-Type", "text/html; charset=utf-8"),
                ("Content-Length", str(len(body))),
            ]
            start_response("200 OK", headers)
            return [body]

        if method == "GET" and path == "/static/style.css":
            status, headers, body = _serve_static(STYLE_PATH)
            start_response(status, headers)
            return [body]

        if method == "POST":
            form = _read_body(environ)
            try:
                if path == "/add-trusted-source":
                    source_id = form.get("source_id", "").strip()
                    if not source_id:
                        app_state.flash("error", "Trusted source identifier is required")
                    else:
                        app_state.registry.add_trusted_source(source_id)
                        app_state.flash("success", f"Added trusted source {source_id}")
                elif path == "/register-identity":
                    identifier = form.get("identifier", "").strip()
                    attestations_raw = form.get("attestations", "")
                    if not identifier:
                        app_state.flash("error", "Identity identifier is required")
                    else:
                        attestations = {
                            att.strip()
                            for chunk in attestations_raw.splitlines()
                            for att in chunk.split(",")
                            if att.strip()
                        }
                        app_state.registry.register_identity(identifier, attestations)
                        app_state.flash(
                            "success",
                            f"Registered identity {identifier} with {len(attestations)} attestations",
                        )
                elif path == "/allocate-stake":
                    account = form.get("account", "").strip()
                    amount_raw = form.get("amount", "0").strip()
                    if not account:
                        app_state.flash("error", "Account is required")
                    else:
                        amount = int(amount_raw)
                        if amount <= 0:
                            raise ValueError("Amount must be positive")
                        app_state.ledger.credit(account, app_state.token.symbol, amount)
                        app_state.token.mint(amount)
                        app_state.flash(
                            "success", f"Allocated {amount} {app_state.token.symbol} to {account}"
                        )
                elif path == "/run-ubi":
                    epoch_raw = form.get("epoch", "0").strip()
                    epoch = int(epoch_raw)
                    if epoch < 0:
                        raise ValueError("Epoch must be non-negative")
                    payouts = app_state.ubi.distribute(epoch) if app_state.ubi else {}
                    app_state.last_epoch = epoch
                    app_state.last_payouts = payouts
                    if payouts:
                        app_state.flash("success", f"Distributed UBI for epoch {epoch}")
                    else:
                        app_state.flash("info", "No payouts were made (no verified identities)")
                elif path == "/draw-lottery":
                    raw_participants = form.get("participants", "")
                    winner_count_raw = form.get("winner_count", "1")
                    participants = [
                        participant.strip()
                        for chunk in raw_participants.splitlines()
                        for participant in chunk.split(",")
                        if participant.strip()
                    ]
                    winner_count = int(winner_count_raw)
                    if app_state.lottery is None:
                        raise ValueError("Lottery not configured")
                    result = app_state.lottery.draw(participants, winner_count)
                    app_state.last_lottery = result
                    app_state.flash(
                        "success",
                        "Lottery seed "
                        + f"{result.seed[:8]}... selected {', '.join(result.winners)}",
                    )
                elif path == "/submit-proposal":
                    identifier = form.get("proposal_id", "").strip()
                    description = form.get("description", "").strip()
                    quorum_raw = form.get("quorum", "0").strip()
                    threshold_raw = form.get("threshold", "0.5").strip()
                    if not identifier:
                        app_state.flash("error", "Proposal identifier is required")
                    else:
                        quorum = int(quorum_raw)
                        threshold = float(threshold_raw)
                        app_state.governance.submit_proposal(identifier, description, quorum, threshold)
                        app_state.flash("success", f"Submitted proposal {identifier}")
                elif path == "/stake-vote":
                    proposal_id = form.get("proposal_id", "").strip()
                    account = form.get("account", "").strip()
                    vote_raw = form.get("vote", "")
                    if not proposal_id or not account:
                        app_state.flash("error", "Proposal and account are required")
                    else:
                        vote = _parse_vote(vote_raw)
                        app_state.governance.cast_stake_vote(proposal_id, account, vote)
                        app_state.flash(
                            "success", f"Recorded stake vote for {account} on {proposal_id}"
                        )
                elif path == "/citizen-vote":
                    proposal_id = form.get("proposal_id", "").strip()
                    identity = form.get("identity", "").strip()
                    vote_raw = form.get("vote", "")
                    if not proposal_id or not identity:
                        app_state.flash("error", "Proposal and identity are required")
                    else:
                        vote = _parse_vote(vote_raw)
                        app_state.governance.cast_citizen_vote(proposal_id, identity, vote)
                        app_state.flash(
                            "success", f"Recorded citizen vote for {identity} on {proposal_id}"
                        )
                else:
                    start_response("404 Not Found", [("Content-Type", "text/plain")])
                    return [b"Not Found"]
            except (KeyError, ValueError) as exc:
                app_state.flash("error", str(exc))
            status, headers, body = _redirect("/")
            start_response(status, headers)
            return [body]

        start_response("405 Method Not Allowed", [("Content-Type", "text/plain")])
        return [b"Method Not Allowed"]

    return app


def run(host: str = "127.0.0.1", port: int = 5000) -> None:
    """Run the SELFNet console using Python's built-in WSGI server."""

    app = create_app()
    with make_server(host, port, app) as server:
        print(f"SELFNet console running on http://{host}:{port}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down console...")


__all__ = ["AppState", "create_app", "run"]


if __name__ == "__main__":
    run()
