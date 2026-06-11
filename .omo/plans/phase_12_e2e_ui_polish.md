# Phase 12: E2E Testing and UI Polish

## TL;DR
This plan covers Phase 12 of the ProofNode project. It focuses on validating the frontend functionality through End-to-End (E2E) testing and refining the user interface to ensure a seamless and robust user experience.

**Objective:** Ensure the React frontend is bug-free, fully responsive, handles loading/error states gracefully, and that all major user flows (Telegram auth, purchasing, copy-trading) are covered by automated tests.
**Non-goals:** Adding new features to the backend or smart contract integration.

## Decision Summary
- **Testing Framework:** Playwright (optimal for mocking Telegram Mini App environments and fast execution).
- **UI Improvements:** Implement skeletons for loading states, comprehensive error boundaries, and toast notifications for feedback.
- **File Ownership:** `frontend/tests/e2e/`, `frontend/src/components/ui/`.

## Files to Edit / Create
- `frontend/package.json` (add Playwright dependencies)
- `frontend/playwright.config.ts` (new)
- `frontend/tests/e2e/auth.spec.ts` (new)
- `frontend/tests/e2e/trading.spec.ts` (new)
- `frontend/src/components/ui/Toaster.tsx` (new)
- `frontend/src/components/ui/Skeleton.tsx` (new)
- Updates to `Leaderboard.tsx`, `Cabinet.tsx`, `TraderProfile.tsx` for loading states.

## TODOs

- [x] **1. Setup Playwright**
  - Install Playwright in the `frontend` directory.
  - Create `playwright.config.ts` with settings to mock Telegram `initData` during tests.
  - Add test scripts to `package.json`.
- [x] **2. Write E2E Tests for Core Flows**
  - Write tests for the TMA Auth flow (mocking Telegram environment variables).
  - Write tests for navigating the Leaderboard, filtering, and viewing Trader Profiles.
  - Write tests for the Cabinet, signal creation/closing, and proxy wallet registration.
  - Write tests for the Premium Upsell flow.
- [x] **3. Implement UI Polish (Loading & Error States)**
  - Create reusable `Skeleton` components for lists and cards.
  - Integrate Skeletons into `Leaderboard.tsx` and `Referrals.tsx` while `isLoading` is true.
  - Implement a global `Toaster` component for displaying success/error messages (replacing native `alert()` calls).
- [x] **4. Responsive Design & Accessibility Audit**
  - Test all views at 320px width (minimum mobile size).
  - Fix any overlapping text or broken layouts.
  - Ensure contrast ratios and focus states meet accessibility standards.
- [x] **5. CI Integration**
  - Add a GitHub Actions / CI step to run Playwright tests against a mocked backend on pull requests.

## QA Scenarios
1. **Test Execution:**
   - Command: `npm run test:e2e` in the `frontend` directory.
   - Expected Evidence: All Playwright tests pass (Auth, Leaderboard, Trading). Test report generated.
2. **UI Loading State:**
   - Action: Throttle network to "Slow 3G" in browser dev tools.
   - Expected Evidence: Skeletons are displayed instead of blank screens while fetching API data.
3. **UI Error Handling:**
   - Action: Force API to return 500 error.
   - Expected Evidence: Graceful error toast message appears instead of breaking the app or showing unhandled promise rejections.

## Next Steps
Next: `start-work .omo/plans/phase_12_e2e_ui_polish.md`
