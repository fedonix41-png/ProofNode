# Fix Shortcomings (Pre-Phase 6)

## TL;DR
**Objective:** Address 9 critical shortcomings identified from gap analysis against the `alphahub_product_concept.md` and technical specifications before moving to Phase 6.
**Non-Goals:** Building out full frontend marketplace flows beyond simple filters. Writing new blockchain parsers.
**Decision Summary:** We will create necessary endpoints, background jobs, and adjust the DB schema minimally (if required) to support categories, referrals, and PnL. We will enforce freemium constraints at the bot worker level and handle 5% commission calculation at the subscription validation level.

## Scope of Work

### P0 (Critical Path)
1. **Proof-of-Trade Verification & Stats**
   - Add endpoint `POST /traders/{id}/wallets` for binding trader wallets (if not already fully covered by the generic `/wallets` endpoint, or alias it for REST conformity).
   - Create a background worker job to calculate `daily_roi`, `winrate`, and `drawdown` by aggregating `wallet_transactions` and upserting into `trader_pnl_history`.

2. **Smart Money Tracker PnL**
   - Add a worker to compute unrealized PnL for `monitored_wallets` based on historical transaction buy/sell sums.
   - Serve these metrics via an endpoint to replace frontend mock values.

### P1 (Monetization & Tiers)
3. **Platform Commission**
   - Implement the 5% platform fee deduction logic inside the payment verification/subscription flow (`subscriptions.py`).
4. **Freemium Logic**
   - Add a limit check: Max 3 `monitored_wallets` for `is_premium = FALSE`.
   - Modify the push notification dispatcher (`bot/consumer.py` / `worker.py`) to delay messages by 10 minutes for free users (using RabbitMQ dead-lettering or a delay plugin, or simply checking timestamps in the worker).

### P2 (Growth & Routing)
5. **Referral Program**
   - Add endpoint `GET /users/referrals` to return referral stats.
   - Add UI for "Refer-to-Unlock" (share link, view referred count).
6. **Public Profiles (Deep Links)**
   - Parse `startapp=profile_123` in the React frontend (TMA context).
   - Route to the specific trader profile instead of the generic Leaderboard.

### P3 (UX Enhancements)
7. **Leaderboard Categorization & Filters**
   - Add `category` enum (Low Risk, Memecoins, Snipers) to `trader_profiles`.
   - Update `GET /traders/profiles` to accept `network`, `category`, `min_winrate`, `min_roi` query parameters.
   - Update `frontend/src/components/Leaderboard.tsx` to include Chip filters and fetch real data.
8. **Signal Creation UI**
   - Add a "Create Signal" form in `Cabinet.tsx` allowing VIP traders to post signals with token addresses.
   - Add `POST /signals` endpoint.

---

## TODOs

### P0 Implementation
- [x] Backend: Add `POST /api/traders/{id}/wallets` endpoint in `routers/traders.py` (alias/wrapper around existing wallet logic).
- [x] Backend: Create `worker_stats.py` (or add to `worker.py`) with a job to compute `trader_pnl_history` (ROI, winrate, drawdown).
- [x] Backend: Create PnL calculator for `monitored_wallets` and expose via `GET /api/wallets/tracker/stats`.

### P1 Implementation
- [x] Backend: In `routers/subscriptions.py`, deduct 5% from the subscription amount before recording the net profit or processing the internal ledger.
- [x] Backend: Enforce 3-wallet limit for free users in `POST /api/wallets/monitor`.
- [x] Bot/Worker: Delay push notifications by 10 mins for `is_premium = FALSE` users.

### P2 Implementation
- [x] Backend: Implement `GET /api/users/referrals` (count `referred_by` matches).
- [x] Frontend: Add Referral UI screen/modal in the TMA.
- [x] Frontend: Add `startapp` deep link parsing to `App.tsx` and route directly to a trader profile view.

### P3 Implementation
- [x] Database: `ALTER TABLE trader_profiles ADD COLUMN category VARCHAR(50);`
- [x] Backend: Update `GET /api/traders` to filter by `category` (Meme, Bluechip, Degen, Volume).
- [x] Frontend: Add category filter pills to `Radar.tsx`.
- [x] Backend & Frontend: Create `POST /api/signals` and add UI to `Cabinet.tsx`.

## QA Scenarios
- **Command:** `pytest tests/test_freemium.py` (To be created)
- **Evidence:** Free users fail to add a 4th monitored wallet. Free users receive delayed notification pushes.
- **Command:** `pytest tests/test_stats_worker.py` (To be created)
- **Evidence:** `trader_pnl_history` is populated correctly based on mock transactions.

Next: `start-work fix_shortcomings_pre_phase6`
