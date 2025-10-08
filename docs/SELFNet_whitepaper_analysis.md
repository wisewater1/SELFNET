# SELFNet Whitepaper Reconstruction and Analysis

This document synthesizes publicly documented mechanics from related decentralized identity, UBI, and randomness protocols to outline a plausible SELFNet architecture. It is not an official SELFNet publication but a technical reconstruction for discussion.

## 1. System Overview

SELFNet can be conceptualized as a modular, intent-centric Layer 1 blockchain that fuses universal basic income (UBI) streaming, democratic governance, and verifiably fair community lotteries. The network relies on three primary asset types:

- **SELF** – a native utility token used for transaction fees, staking, and treasury governance.
- **CPT (Civic Participation Token)** – a non-transferable credential token that provides one-person-one-vote governance and enables eligibility for UBI disbursements.
- **MSR (Monetary Supply Rate)** – an algorithmic parameter that controls the pace of UBI issuance, similar to the minting cadence used in streaming UBI systems.

## 2. Identity and Proof-of-Personhood Layer

Delivering UBI fairly requires a robust identity verification pipeline that balances sybil-resistance with privacy:

1. **Submission** – participants register with biometric or video attestations and stake a refundable bond to deter spam.
2. **Community Review** – registrants are challenged and verified by randomly selected reviewers who draw on a decentralized court or reputation-based arbitration module.
3. **Zero-Knowledge Proofs** – once verified, members receive CPT credentials that can be presented through ZK-proofs, proving "human membership" without exposing personal data.
4. **Revocation and Appeals** – challenge windows and appeal processes help remove fraudulent entries while protecting legitimate users.

## 3. Token Economics

### 3.1 SELF Token

- Acts as the base asset for fee markets and validator staking.
- Secures the network via delegated proof-of-stake, with validators slashed for downtime or misbehavior.
- Grants governance influence in the economic (token-weighted) chamber.
- Feeds into the treasury that funds development, UBI buffers, and lottery liquidity.

### 3.2 CPT Token

- Non-transferable, soulbound credential distributed one-per-human.
- Enables participation in identity-weighted governance and access to UBI streams.
- Can be revoked upon verified fraud, cutting off UBI streams and governance rights.

### 3.3 Monetary Supply Rate (MSR)

- Defines the base UBI accrual per CPT holder (e.g., X units per hour).
- Adjusts dynamically using on-chain metrics (participation, treasury reserves, inflation targets).
- Incorporates demurrage to discourage hoarding and maintain velocity; idle balances decay gently into the communal treasury.

## 4. UBI Streaming Mechanics

1. **Stream Initialization** – upon verification, a UBI streaming contract begins accruing SELF-denominated rewards at the MSR rate.
2. **Claim Windows** – recipients periodically claim accrued balances; demurrage activates on balances older than a threshold.
3. **Treasury Backing** – a portion of block rewards, transaction fees, and staking penalties feed the UBI pool to maintain solvency.
4. **Emergency Brakes** – governance can temporarily throttle the MSR during macro shocks to protect token stability, subject to identity-chamber approval to avoid abuse.

## 5. VRF-Powered Lottery Module

- **Funding** – collects a programmable fraction of transaction fees and voluntary contributions.
- **Randomness** – uses a verifiable random function (VRF) oracle to produce unbiased, auditable draws.
- **Eligibility** – CPT holders automatically participate, with weightings influenced by civic contributions (e.g., participation in reviews or governance).
- **Distribution** – winnings are streamed rather than lump-sum to reduce volatility and promote consistent income supplements.
- **Transparency** – all draws, proofs, and payouts are posted on-chain for community auditability.

## 6. Governance Architecture

SELFNet can deploy a bicameral DAO to balance economic and civic interests:

- **Stakeholder Chamber** – SELF token holders vote proportionally to stake, managing protocol upgrades, validator sets, and treasury allocations.
- **Civic Chamber** – CPT holders exercise equal-weight voting, overseeing identity policy, MSR adjustments, and lottery parameters.
- **Joint Approval** – critical proposals (e.g., MSR overhauls) require approval in both chambers to prevent plutocratic or populist capture.
- **Deliberation Tools** – quadratic funding, optimistic governance, and reputation scores incentivize participation and nuanced decision-making.

## 7. Smart Contract Architecture

SELFNet benefits from modular upgradeability via a diamond proxy (EIP-2535) or equivalent facet-based system:

- **Core Facet** – handles ownership, access control, and upgrade orchestration.
- **Token Facets** – implement ERC-20 (SELF) and soulbound (CPT) logic.
- **Identity Facet** – manages registry, verification workflows, and revocations.
- **UBI Facet** – controls MSR schedules, demurrage, and streaming claims.
- **Lottery Facet** – integrates VRF randomness, ticket weighting, and payout scheduling.
- **Governance Facet** – coordinates proposal submission, voting tallies, and execution pipelines.

Rigorous auditing, invariant testing, and formal verification are required to secure interactions across facets, especially around delegatecalls and shared storage.

## 8. Security and Risk Management

- **Sybil Attacks** – mitigated via multi-layer verification, economic bonds, and ongoing community audits.
- **Economic Instability** – MSR governors monitor inflation and adjust rates; circuit breakers pause emissions if treasury coverage drops below thresholds.
- **Lottery Abuse** – transparent randomness proofs and capped participation prevent manipulation; AML screening satisfies regulatory expectations.
- **Smart Contract Exploits** – bug bounty programs and staged upgrade processes (with time-locks) reduce exploit risk.

## 9. Societal and Regulatory Considerations

- **Inclusion** – hybrid verification (digital plus community attestation) aims to include under-documented populations without sacrificing security.
- **Financial Compliance** – UBI flows and lotteries must respect regional regulations; compliance oracles can gate certain jurisdictions if required.
- **User Experience** – intent-centric wallets abstract gas management, enabling mainstream accessibility and reducing UX friction.

## 10. Open Questions

- How is the MSR algorithm tuned to balance inflation, treasury solvency, and livable income levels?
- What safeguards stop governance capture by either capital holders or coordinated civic groups?
- How can privacy-preserving identity be reconciled with compliance demands across jurisdictions?
- Which cross-chain bridges or fiat on-ramps ensure liquidity for UBI recipients in diverse markets?

## 11. Conclusion

While speculative, this reconstructed design demonstrates how SELFNet could blend identity, UBI, and verifiable randomness into a cohesive economic network. The model depends on robust proof-of-personhood, carefully calibrated monetary policy, and transparent, bicameral governance. Continued research, simulation, and community feedback are essential before deploying such a socio-technical system at scale.
