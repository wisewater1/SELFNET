# SELFNET

SELFNet 2.0 is a modular, privacy-preserving economic network that converts on-chain activity into UBI and community wealth, rewards verified human contribution, and keeps power balanced through two-house governance and strong risk controls.

## Documentation

- [SELFNet Whitepaper Reconstruction and Analysis](docs/SELFNet_whitepaper_analysis.md)

## Simulation Toolkit

This repository includes a Python package that prototypes the core mechanisms of SELFNet:

- Identity registry with trust-based verification thresholds.
- Token ledger and Monetary Supply Rate (MSR) policy primitives.
- UBI stream scheduler that mints CPT tokens for verified citizens.
- VRF-inspired lottery awarding additional SELF token rewards.
- Two-house governance simulator combining stake-weighted and citizen votes.

## Interactive Console

Spin up a lightweight, dependency-free web console that sits on top of the
simulation toolkit and lets you experiment with identities, UBI, lotteries, and
governance in real time:

```bash
pip install -e .[dev]
python -m selfnet.ui.app
```

The console keeps simulation state in memory. Use the provided forms to add
trusted sources, register identities, trigger UBI epochs, allocate stake, run
VRF-style lotteries, and conduct dual-house votes. Refreshing the page preserves
state until the server is restarted.

Install the developer dependencies and run the test suite with:

```bash
pip install -e .[dev]
pytest
```
