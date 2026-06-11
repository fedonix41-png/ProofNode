# ASW Plan: ProofNode Phase 4 - React 19 Telegram Mini App & Client-Side SSS

## TL;DR
Establish the **ProofNode** (AlphaHub) Telegram Mini App (TMA) frontend using React 19, TypeScript, Vite, and Vanilla CSS. Implement a premium, responsive, glassmorphic layout styled to seamlessly integrate with Telegram's theme variables. Build the three core tabs: **Radar (Smart Money)**, **Leaderboard (The Arena)**, and **Cabinet (Author Console)**. Develop a secure client-side Shamir's Secret Sharing (SSS) utility so that user private keys for 1-Click Copy-Trading are split in browser RAM, ensuring the server only ever receives and stores a single isolated share (Share 2).

---

## Objective
To build a highly visual, premium, and secure frontend that:
1. Integrates with the Telegram WebApp SDK to load native theme settings, user profiles, and viewport properties.
2. Implements a CSS-variable-based layout with a bottom navigation bar, offering responsive design and glassmorphic card elements.
3. Provides a **Leaderboard Tab** displaying trader winrates, historical PnL charts (using canvas/SVG), and tariff subscription checkouts using `@tonconnect/ui-react` for wallet interactions.
4. Provides a **Radar Tab** allowing users to search and track smart-money addresses, toggle push notification preferences, and inspect transaction histories.
5. Provides a **Cabinet Tab** enabling traders to register their Proof-of-Trade wallets and configure access subscription prices.
6. Employs **Client-Side SSS key splitting** so that users can configure 1-Click Copy-Trading by generating/inputting their private key, splitting it into 3 shares, sending only Share 2 to the server, and storing Share 1 locally.
7. Validates components and routing via component and system tests.

---

## Non-Goals
- Deploying the frontend to a production domain (Vercel/GitHub Pages/Firebase Hosting) which is scheduled for Phase 7.
- Connecting to live mainnet blockchain nodes or real on-chain transaction broads (Phase 6).
- Integrating real AWS KMS or Google Cloud HSM APIs (Phase 7).

---

## Decision Summary
- **Frontend Stack**: React 19 + TypeScript + Vite.
  - *Initialization*: Using `npx -y create-vite@latest frontend --template react-ts` to scaffold the project inside a `frontend` folder.
- **Styling**: Vanilla CSS with custom properties (CSS variables) to inherit dynamic colors from Telegram WebApp API (e.g. `--tg-theme-bg-color`, `--tg-theme-button-color`). Default fallback style is dark slate/glassmorphism.
- **Wallet Connection**: `@tonconnect/ui-react` for official TON Connect integration.
- **Client-Side SSS (2-of-3)**: Implemented in pure TypeScript (Lagrange interpolation in finite field $GF(2^8)$ or similar field representation) running entirely in the user's browser/TMA memory.
  - **Share 1**: Stored locally on the user's device (`localStorage` or Telegram's CloudStorage API).
  - **Share 2**: Saved on the ProofNode server via `POST /api/wallets/sss/register`.
  - **Share 3**: Shown to the user once to write down or back up.
- **Mocking**: WebApp Mock layer to simulate Telegram environment variables when running in a standard desktop browser.

---

## Files to Edit & Create

### [NEW] Frontend Scaffolding & Setup
- [package.json](file:///home/ozzy/Документы/ProofNode/frontend/package.json) - React 19, TypeScript, Vite, `@tonconnect/ui-react`, `lucide-react` for icons.
- [index.html](file:///home/ozzy/Документы/ProofNode/frontend/index.html) - Main entry HTML mounting the app and loading the Telegram WebApp JS script `<script src="https://telegram.org/js/telegram-web-app.js"></script>`.
- [vite.config.ts](file:///home/ozzy/Документы/ProofNode/frontend/vite.config.ts) - Vite build config, including development server proxy settings to route `/api` to the backend.

### [NEW] CSS System & Theme
- [index.css](file:///home/ozzy/Документы/ProofNode/frontend/src/index.css) - Vanilla CSS stylesheet containing font setup, scrollbar styling, glassmorphic card classes, and Telegram variable definitions.

### [NEW] Core Components & Views
- [main.tsx](file:///home/ozzy/Документы/ProofNode/frontend/src/main.tsx) - React root initialization, wrapping the application in `TonConnectUIProvider`.
- [App.tsx](file:///home/ozzy/Документы/ProofNode/frontend/src/App.tsx) - App layout, bottom tab navigation coordinator, and Telegram theme listener.
- [Navigation.tsx](file:///home/ozzy/Документы/ProofNode/frontend/src/components/Navigation.tsx) - Bottom navigation bar containing icons for Radar, Marketplace, and Cabinet.
- [Radar.tsx](file:///home/ozzy/Документы/ProofNode/frontend/src/components/Radar.tsx) - Wallet tracking view, detailed transaction sheet, and push notifications switch.
- [Leaderboard.tsx](file:///home/ozzy/Документы/ProofNode/frontend/src/components/Leaderboard.tsx) - Leaderboard view, interactive SVG profit trend charts, and subscription checkout.
- [Cabinet.tsx](file:///home/ozzy/Документы/ProofNode/frontend/src/components/Cabinet.tsx) - B2B cabinet, trader wallet tracking configuration, and SSS client-side splitting panel.

### [NEW] Client-Side SSS Utility
- [sss.ts](file:///home/ozzy/Документы/ProofNode/frontend/src/utils/sss.ts) - Math routines for splitting a hex key into 3 shares and reconstructing it from 2.

### [NEW] Mock Server Gateway Configuration
- [mockTelegram.ts](file:///home/ozzy/Документы/ProofNode/frontend/src/utils/mockTelegram.ts) - Stub for `window.Telegram` when running outside of a native Telegram client.

### [NEW] Testing Suite
- [test_frontend_sss.ts](file:///home/ozzy/Документы/ProofNode/frontend/src/utils/test_frontend_sss.ts) - Unit tests asserting frontend SSS correctness.

---

## TODOs

- [ ] **Frontend Initialization & Configuration**
  - Run `npx -y create-vite@latest frontend --template react-ts` to initialize the project directory.
  - Install dependencies: `@tonconnect/ui-react` and `lucide-react`.
  - Update `frontend/vite.config.ts` to include a local dev server proxy routing requests from `/api` to the backend on `http://127.0.0.1:8000`.
  - *Commit guidance*: "frontend: initialize react 19 + vite project scaffold"

- [ ] **CSS Styling & Theme Configuration**
  - Implement `frontend/src/index.css` defining premium theme variables:
    - Background: `--bg-color: var(--tg-theme-bg-color, #121214)`
    - Secondary/Cards: `--secondary-bg: var(--tg-theme-secondary-bg-color, #1a1a1e)`
    - Neon Accents: `--accent-blue: #00a2ff`, `--accent-green: #2ed573`, `--accent-red: #ff4757`
  - Add utility styles for glassmorphism (`backdrop-filter: blur(12px)`), custom scrollbars, and haptic button tap scaling.
  - *Commit guidance*: "frontend: set up index.css with telegram dark neon theme variables"

- [ ] **Mock Telegram SDK Setup**
  - Implement `frontend/src/utils/mockTelegram.ts` to mock `window.Telegram.WebApp` when the app is opened in standard desktop web browsers.
  - Support setting mock user details, theme color toggles, and mock haptic triggers.
  - *Commit guidance*: "frontend: add mock telegram webapp environment utility"

- [ ] **Client-Side SSS Mathematics**
  - Implement `frontend/src/utils/sss.ts` with SSS 2-of-3 logic in JavaScript:
    - `splitKey(privateKeyHex: str) -> [Share1, Share2, Share3]`
    - `reconstructKey(shareA: str, shareB: str) -> privateKeyHex`
  - Write a simple browser test script `test_frontend_sss.ts` to assert that sharing works and fails when under 2 shares are present.
  - *Commit guidance*: "frontend: implement client-side shamirs secret sharing key splitter"

- [ ] **Main Layout and Navigation Components**
  - Create `frontend/src/components/Navigation.tsx` implementing a bottom tab bar with transition animations.
  - Create `frontend/src/App.tsx` holding navigation state (`radar` | `leaderboard` | `cabinet`) and reading Telegram WebApp theme settings dynamically.
  - *Commit guidance*: "frontend: build bottom navigation bar and primary layout"

- [ ] **Radar (Smart Money) View**
  - Create `frontend/src/components/Radar.tsx`:
    - Add search bar with network selector (TON, Solana, Base) and wallet insertion button.
    - Show tracked wallets card listing: short address, Sparkline SVG chart of profit trend, and toggles for push alerts.
    - Implement a slide-up drawer detailing wallet balance, token lists, and a list of last 5 transactions.
  - *Commit guidance*: "frontend: implement radar tab with wallet search and transaction drawer"

- [ ] **Marketplace & Leaderboard View**
  - Create `frontend/src/components/Leaderboard.tsx`:
    - List verified traders, winrates, and monthly ROIs.
    - Draw interactive charts showing PnL performance trends.
    - Implement subscription purchase checkout using `@tonconnect/ui-react` for TON wallet Connect, initiating a transaction signature request, receiving the transaction BOC, and posting to `/api/subscriptions/verify`.
  - *Commit guidance*: "frontend: implement marketplace tab with leaderboard and purchase verification"

- [ ] **Cabinet View**
  - Create `frontend/src/components/Cabinet.tsx`:
    - Let admins register their channel IDs, add monitoring wallets, and create billing tariffs.
    - Implement the security section allowing user to input a mock private key: run the client-side SSS logic, transmit ONLY Share 2 to `/api/wallets/sss/register`, save Share 1 to local storage, and display Share 3 to the user as a backup string.
  - *Commit guidance*: "frontend: implement cabinet tab with tariff setup and SSS key setup"

---

## QA Scenarios

### Scenario 1: Local Development Server Boot
- **Command**:
  ```bash
  cd frontend
  npm install
  npm run dev -- --host 127.0.0.1 --port 3000
  ```
- **Expected Evidence**:
  - The terminal prints that the Vite server is running on `http://127.0.0.1:3000`.
  - Opening the URL in a browser displays the glassmorphic dark theme app with functional tab transitions.

### Scenario 2: Client-side SSS Encryption Verification
- **Command**:
  - Open the Cabinet Tab, enter a mock private key `1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef` and click "Set up 1-Click Copying".
- **Expected Evidence**:
  - Web console logs show that the key was split into three shares.
  - LocalStorage contains `sss_share_1`.
  - Network logs confirm a POST was sent to `/api/wallets/sss/register` containing *only* `server_share` (Share 2) and *no* part of the original key.
  - UI displays an alert showing "Share 3: [Back-up share]" asking the user to copy it.

### Cleanup Receipt
- **Command**:
  - Press `Ctrl+C` to terminate the Vite development server.
- **Expected Evidence**:
  - Port `3000` is freed and the process closes.

---

## Privacy & Package Safeguards
- SSS private keys must be processed entirely in ephemeral React state/RAM. Never log the private key or full key reconstruction in the console logs.
- Prevent caching/local storage of the reconstructed private key or Share 3.

Next: `start-work proofnode_phase4`
