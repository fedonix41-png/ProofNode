# ASW Plan: ProofNode Phase 7 - Monetization & Growth Features

## TL;DR
Complete the monetization layer from the original ТЗ: implement the referral program (Refer-to-Unlock), B2C premium subscription with $15/month tier, automatic commission transfers to platform treasury, and marketing growth hooks.

---

## Objective
To finalize all monetization features specified in the original ТЗ:
1. Implement referral program: users earn +2 wallet slots per invited user who completes an action.
2. Build B2C premium subscription flow: $15/month for unlimited wallets and instant notifications.
3. Automate 5% platform commission transfers to treasury wallet.
4. Add growth tracking and on-chain leaderboard caching for marketing.

---

## Non-Goals
- Automated copy-trading execution (Phase 8).
- KMS production hardening (Phase 9).
- Multi-language support.
- Mobile app outside Telegram Mini App.

---

## Decision Summary
- **Referral Program**:
  - Each user has unique `referral_code` (already exists in DB).
  - Invited user must connect wallet or complete one trade.
  - Referrer gains `referral_credits` (+2 wallet slots per invite).
  - Track `users.referred_by` and `referral_credits` fields.
- **B2C Premium**:
  - New table `premium_subscriptions` for B2C tier.
  - Payment via TON (TonConnect) or Telegram Stars.
  - Premium grants: unlimited wallets, instant notifications, access to "Top 100 wallets" list.
- **Commission Transfers**:
  - Cron job (daily) aggregates platform 5% commission.
  - Transfer to `PLATFORM_TREASURY_ADDRESS` via batch transaction or manual settlement.
  - Log in `commission_payouts` table.
- **Growth Hooks**:
  - Endpoint returning "Top gainers of the week" for external marketing.
  - Cache leaderboard results in Redis with 1-hour TTL.

---

## Files to Edit & Create

### [MODIFY] Database Schema
- [init_db.sql](file:///home/ozzy/Документы/ProofNode/database/init_db.sql) - Add `referral_credits INT DEFAULT 0` to users, add `premium_subscriptions` table, add `commission_payouts` table.

### [MODIFY] Configuration
- [config.py](file:///home/ozzy/Документы/ProofNode/backend/app/config.py) - Add `PREMIUM_PRICE_TON`, `PREMIUM_PRICE_STARS`, `REFERRAL_CREDIT_PER_INVITE`.

### [NEW] Services
- [referral.py](file:///home/ozzy/Документы/ProofNode/backend/app/services/referral.py) - Referral code generation, credit tracking, wallet slot calculation.
- [commission.py](file:///home/ozzy/Документы/ProofNode/backend/app/services/commission.py) - Daily aggregation and payout scheduling.

### [MODIFY] Routers
- [subscriptions.py](file:///home/ozzy/Документы/ProofNode/backend/app/routers/subscriptions.py) - Add B2C premium purchase endpoint.
- [wallets.py](file:///home/ozzy/Документы/ProofNode/backend/app/routers/wallets.py) - Use referral credits in wallet limit calculation.
- [traders.py](file:///home/ozzy/Документы/ProofNode/backend/app/routers/traders.py) - Add `GET /traders/top-week` endpoint for marketing.

### [MODIFY] Frontend
- [Cabinet.tsx](file:///home/ozzy/Документы/ProofNode/frontend/src/components/Cabinet.tsx) - Add referral section with shareable link and credit display.
- [Radar.tsx](file:///home/ozzy/Документы/ProofNode/frontend/src/components/Radar.tsx) - Show premium upsell banner for free users.
- [Navigation.tsx](file:///home/ozzy/Документы/ProofNode/frontend/src/components/Navigation.tsx) - Add premium badge indicator.

### [NEW] Frontend Components
- [ReferralCard.tsx](file:///home/ozzy/Документы/ProofNode/frontend/src/components/ReferralCard.tsx) - Referral link display and stats.
- [PremiumUpsell.tsx](file:///home/ozzy/Документы/ProofNode/frontend/src/components/PremiumUpsell.tsx) - Premium benefits card and purchase flow.

### [MODIFY] Bot
- [scheduler.py](file:///home/ozzy/Документы/ProofNode/bot/scheduler.py) - Add daily commission aggregation task.

### [NEW] Testing
- [test_monetization.py](file:///home/ozzy/Документы/ProofNode/tests/test_monetization.py) - Tests for referral credits, premium purchase, commission calculation.

---

## TODOs

- [ ] **Database Schema Updates**
  - Add to `init_db.sql`:
    ```sql
    ALTER TABLE users ADD COLUMN IF NOT EXISTS referral_credits INT DEFAULT 0;
    
    CREATE TABLE IF NOT EXISTS premium_subscriptions (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        status VARCHAR(20) DEFAULT 'ACTIVE',
        expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
        payment_tx_hash VARCHAR(128),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS commission_payouts (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        period_start TIMESTAMP WITH TIME ZONE NOT NULL,
        period_end TIMESTAMP WITH TIME ZONE NOT NULL,
        total_volume NUMERIC(40, 18),
        commission_amount NUMERIC(40, 18),
        payout_tx_hash VARCHAR(128),
        status VARCHAR(20) DEFAULT 'PENDING',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    ```
  - Run migration: `docker compose exec db psql -U postgres -d proofnode -f /docker-entrypoint-initdb.d/init_db.sql`
  - *Commit guidance*: "db: add referral credits, premium subscriptions, and commission payouts tables"

- [ ] **Referral Service**
  - Create `backend/app/services/referral.py`:
    - `generate_referral_link(user_id)` → returns `t.me/AlphaHubBot/app?startapp=ref_{code}`
    - `apply_referral_credit(referrer_id, referred_id)` → increments `referral_credits`
    - `get_max_wallets(user)` → returns 3 + referral_credits * 2 (or unlimited if premium)
  - *Commit guidance*: "feat: implement referral credit system for wallet slots"

- [ ] **Referral UI**
  - Update `Cabinet.tsx` with referral section:
    - Display user's referral link with copy button.
    - Show current referral count and earned wallet slots.
  - Update `App.tsx` to handle `startapp=ref_{code}` and apply referral on first action.
  - *Commit guidance*: "feat: add referral program UI with shareable links"

- [ ] **B2C Premium Subscription**
  - Add endpoint `POST /subscriptions/premium`:
    - Accept TON or Stars payment.
    - Create `premium_subscriptions` record with 30-day expiry.
    - Update `users.is_premium = true`.
  - Update `wallets.py` to check premium status for unlimited slots.
  - Update `bot/consumer.py` to check premium for instant notifications.
  - *Commit guidance*: "feat: add B2C premium subscription tier"

- [x] **Premium Purchase UI**
  - Create `PremiumUpsell.tsx`:
    - Benefits list: unlimited wallets, instant alerts, top 100 list.
    - Price: $15/month in TON or Stars.
    - TonConnect transaction flow.
  - Show upsell banner in `Radar.tsx` for free users.
  - *Commit guidance*: "feat: add premium subscription purchase flow"

- [x] **Commission Aggregation**
  - Create `backend/app/services/commission.py`:
    - `aggregate_daily_commission()` → sum 5% from subscription payments.
    - `schedule_payout(amount)` → create pending `commission_payouts` record.
  - Add to `bot/scheduler.py`:
    - Daily cron at 00:00 UTC calling `aggregate_daily_commission()`.
  - *Commit guidance*: "feat: add daily platform commission aggregation"

- [x] **Top Traders Endpoint**
  - Add `GET /traders/top-week`:
    - Return top 10 traders by ROI in last 7 days.
    - Include basic stats: slug, name, ROI, winrate.
    - Cache in Redis with 1-hour TTL.
  - *Commit guidance*: "feat: add weekly top traders endpoint for marketing"

- [x] **Integration Tests**
  - Create `tests/test_monetization.py`:
    - Test referral credit application.
    - Test wallet limit calculation with credits.
    - Test premium subscription creation.
    - Test commission aggregation.
  - Run: `PYTHONPATH=. uv run pytest tests/test_monetization.py -v`.
  - *Commit guidance*: "test: add tests for referral and premium features"

---

## QA Scenarios

### Scenario 1: Referral Credit Application
- **Command**:
  ```bash
  PYTHONPATH=. uv run pytest tests/test_monetization.py::test_referral_credit -v
  ```
- **Expected Evidence**: Test passes, showing referrer gains +2 wallet slots after referred user connects wallet.

### Scenario 2: Premium Purchase Flow
- **Command**:
  - In TMA, navigate to Cabinet → Premium section.
  - Click "Upgrade to Premium ($15/month)".
  - Complete mock TonConnect transaction.
- **Expected Evidence**: User's `is_premium` flag set to true, premium badge appears in navigation.

### Scenario 3: Commission Calculation
- **Command**:
  ```bash
  PYTHONPATH=. uv run pytest tests/test_monetization.py::test_commission_aggregation -v
  ```
- **Expected Evidence**: Test passes, showing 5% commission correctly calculated from mock subscription payments.

### Scenario 4: Wallet Limit Enforcement
- **Command**:
  ```bash
  PYTHONPATH=. uv run pytest tests/test_monetization.py::test_wallet_limit_with_credits -v
  ```
- **Expected Evidence**: Test passes, showing user with 2 referrals can create up to 7 wallets (3 base + 4 from credits).

### Cleanup Receipt
- **Command**: `docker compose down -v`
- **Expected Evidence**: All test containers and volumes removed.

---

## Privacy & Package Safeguards
- Never expose user referral codes in public logs.
- Sanitize payment transaction hashes before logging.
- Use environment variables for all pricing and treasury addresses.

Next: `start-work proofnode_phase8`
