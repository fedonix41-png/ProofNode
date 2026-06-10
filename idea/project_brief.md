# Project Brief: AlphaHub

> Complete Strategic Foundation

**Created:** 2026-06-10  
**Author:** Mary (📊 Analyst BMad Agent)  
**Brief Type:** Complete  

---

## Vision

To build a decentralized Web3 trust protocol and investment co-pilot in Telegram that resolves the chronic trust gap in social trading. By substituting manual signal entry with **Proof-of-Trade (on-chain trade verification)** and replacing manual order entry with **1-Click / Automated Copy-Trading**, AlphaHub empowers users to copy elite crypto traders securely, instantly, and transparently.

---

## Positioning Statement

For retail Web3 investors seeking profitable, scam-free trading ideas, and for signal channel administrators looking to monetize their trade records honestly, **AlphaHub** is a Telegram Mini App Social Trading Hub that verifies real trades on-chain and routes them directly to automated proxy trading routers. 

Unlike telega.in, custom paywall bots, or manual whale trackers which suffer from delay, friction, and manipulation, our product offers **instant zero-fraud verification** combined with **non-custodial session-key execution**.

**Breakdown:**

- **Target Customer:** Crypto traders looking to copy profitable on-chain activity; administrators of Telegram signal channels looking to automate paywall management.
- **Need/Opportunity:** High rate of fraud among manual signal providers; exit liquidity issues due to delays in manually buying tokens after notifications.
- **Category:** Web3 Social Finance (Social-Fi) / Telegram Mini App (TMA).
- **Key Benefit:** Trustless performance metrics and near-instant trade mirroring.
- **Differentiator:** Autogen Proof-of-Trade tracing + hybrid key security (Shamir's Secret Sharing + KMS limited proxy wallets).

---

## Business Model

**Type:** Hybrid B2B / B2C (Transactional + Subscription)

### Business Customer Profile (B2B)
Telegram channel admins (2k-15k subscribers) providing VIP signals or premium alpha. They are looking to increase billing conversion and prove their trading performance without manual spreadsheet recording.

### Buying Roles

| Role         | Description       |
| ------------ | ----------------- |
| **Buyer**    | The channel admin who pays 5% platform commission on paywall entries in exchange for automated billing and verified track records. |
| **Champion** | Pro traders looking to rank on "The Arena" leaderboard to organically gain subscribers. |
| **User**     | Admins utilizing the signal creation and client management UI. |

---

## Ideal Customer Profile (ICP)
Retail Web3 traders, ranging from "degens" trading memecoins on Base/Solana to active investors in the TON ecosystem. They have moderate to high risk tolerance and seek to copy trade with a controlled budget.

### Secondary Users
- Passive investors looking to allocate small budgets to copy verified traders automatically.
- Blockchain researchers looking to monitor large "whale" wallet movements.

---

## Success Criteria

1. **Transaction Processing SLA:** Webhook to RabbitMQ ingestion in `< 200ms`. Event decoding to database execution in `< 1.5s`.
2. **Copy-Trading Latency:** Target execution of user copy-trade within `< 3.0s` from the trigger transaction's inclusion in block.
3. **Data Efficiency:** 70% storage savings on database chunks via TimescaleDB compression policies.
4. **Acquisition Target:** Onboard 50+ active signal channel admins and achieve $100k+ in copy-trading transaction volume in Month 1 of public beta.

---

## Competitive Landscape

- **Telegram Paywall Bots (Donate, VIPLiner):** Good for billing, but zero trading integration or signal verification. Easy for scam admins to hide losses.
- **On-chain Trackers (Cielo, Lookonchain):** Excellent for tracking, but lack direct copy-trading or CRM integration for VIP channels.
- **EVM Copy-Trading Platforms (Banana Gun, Maestro):** Powerful execution bots, but lack social trust structures, Telegram channel integration, and fail to verify channel owner metrics.

### Our Unfair Advantage
The **Proof-of-Trade Protocol**. By directly linking a channel's subscription paywall to the admin's on-chain trading address (with Trace ID verification), we make it impossible to fabricate win rates, making AlphaHub the gold standard of credibility.

---

## Constraints

1. **Telegram Sandbox Limits:** Mini App viewport sizes, storage restrictions, and memory limits.
2. **TON Asynchronous Architecture:** Transaction processing must handle split internal messages (traces) across multiple blocks rather than atomic EVM execution blocks.
3. **Security Constraints:** Server cannot store raw private keys for user copy-trading without SSS or KMS encapsulation.
4. **App Store Commissions:** Telegram Stars billing must account for 30% platform commissions and 21-day holding periods.

---

## Platform & Device Strategy

**Primary Platform:** Telegram Mini App (TMA) Framework

**Supported Devices:**
- iOS, Android, and Telegram Desktop client.

**Device Priority:** Mobile First (90%+ of TG Mini App users are on mobile).

**Interaction Models:**
- Simple 1-click execution buttons.
- Clean tab navigation (Radar, Marketplace, Author Cabinet).

**Technical Requirements:**
- **Offline Functionality:** Read-only cached views of portfolio ROI via LocalStorage.
- **Native Features:** Haptic feedback API, Telegram WebApp expanded viewport, push notifications.

**Platform Rationale:**
Telegram offers immediate distribution and native access to users' Web3 wallets (TON Connect) and social networks.

---

## Tone of Voice

**For UI Microcopy & System Messages**

### Tone Attributes

1. **Objective**: Grounded in real on-chain data, avoiding hype or exaggerated win promises.
2. **Transparent**: Clear warnings on transaction risks, slippage, and fees.
3. **Direct**: Action-oriented messages suited to fast-paced trading.

### Examples

**Error Messages:**
- ✅ "Transaction failed: Slippage limit exceeded (Max 5.0%). Try adjusting threshold."
- ❌ "Oh no! Something went wrong with the blockchain. Please try again."

**Button Text:**
- ✅ "Copy Trade (10 TON)"
- ❌ "Click here to buy tokens now"

**Empty States:**
- ✅ "No wallets added yet. Enter a TON, SOL, or Base address to begin tracking."
- ❌ "It's empty here! Add some whales!"

### Guidelines

**Do:**
- Cite exact coin symbols, amounts, and networks.
- Clearly present gas and copy-trading execution fee markups.

**Don't:**
- Use vague phrases like "your trade will happen soon" — always display current pending status.

---

## Business Context

- **Primary Goal:** Provide a secure, verified social copy-trading platform in Telegram.
- **Solution:** Integrated Web3 indexing webhook gateway, TimescaleDB analytics, and non-custodial copy-trade signing.
- **Target Users:** Active Telegram Web3 traders and channel owners.

---

## Next Steps

This complete brief provides strategic foundation for all design work:

- [x] **Phase 1: Project Scaffolding & Webhook Gateway** - Complete (Amelia / Dev)
- [ ] **Phase 2: Product Requirement Document (PRD) Expansion** - Technical specifications for transaction decoders
- [ ] **Phase 3: Test Design & QA Scaffolding** - Murat / QA
- [ ] **Phase 4: Frontend UI Specifications** - Sally / UX
