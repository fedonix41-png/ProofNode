# Plan: Telegram Mini App Layout Fixes

## TL;DR
This plan details how to resolve layout and scrolling bugs inside the Telegram Mini App (TMA) viewport on mobile and desktop. It locks the viewport to prevent dynamic page elastic bouncing, fixes horizontal scroll leakage caused by absolute mesh background overflow on WebKit/Safari, and locks the bottom navigation bar to the bottom of the screen without dynamic scroll jitter.

---

## Objective
To ensure the `ProofNode` frontend renders pixel-perfect, matches the prototype design exactly, prevents horizontal scroll leakages, and keeps the bottom navigation bar strictly visible at the bottom of the viewport on all devices (mobile and desktop).

---

## Non-Goals
- Restructuring the core features of the screens (Radar, Cabinet, Leaderboard).
- Adjusting mock data or API endpoints.

---

## Decision Summary

1. **Lock the Document Viewport**
   - Apply strict `position: fixed; top: 0; bottom: 0; left: 0; right: 0; overflow: hidden;` constraints to `html` and `body` in `index.css`. This prevents the browser wrapper in TMA (especially iOS WebKit) from registering page-level elastic scroll boundaries.

2. **Refactor Background Gradients**
   - Move absolute mesh gradients from `App.tsx`'s main wrapper into a separate `fixed inset-0 overflow-hidden pointer-events-none -z-10` container. This completely isolates large blur elements from the layout flow, preventing them from extending the body width and causing the buggy horizontal scroll.

3. **Flex-Anchored Bottom Navigation**
   - Refactor `.app-container` to use absolute bounds `position: absolute; top: 0; bottom: 0; left: 50%; transform: translateX(-50%);` matching the viewport boundaries.
   - Lay out the header, main scroll area, and bottom navigation bar naturally inside `.app-container` using Flexbox column flow. By making `<main>` `flex-1 overflow-y-auto` and the navigation menu a natural flex child with `flex-shrink: 0`, the menu remains strictly anchored to the bottom of the visible screen without floating, jittering, or requiring any padding/fixed hacks.

4. **Safari Clipping Stacking Context**
   - Add `isolation: isolate !important;` to `.app-container` to force WebKit/Safari to clip negative z-index elements within the container boundaries, solving the WebKit overflow rendering bug.

---

## Files to Edit
- `frontend/src/index.css`
- `frontend/src/App.tsx`

---

## TODOs

- [ ] **Lock global html/body viewport**
  - Edit `frontend/src/index.css` to restrict the viewport bounds and prevent bounce effects.
  - Apply `position: fixed !important; top: 0 !important; bottom: 0 !important; left: 0 !important; right: 0 !important; overflow: hidden !important; width: 100% !important; height: 100% !important;` to both `html` and `body` rules.

- [ ] **Define absolute TMA App Container**
  - Update `.app-container` in `index.css` to use absolute placement:
    ```css
    .app-container {
      position: absolute !important;
      top: 0 !important;
      bottom: 0 !important;
      left: 50% !important;
      transform: translateX(-50%) !important;
      width: 100% !important;
      max-width: 448px !important;
      display: flex !important;
      flex-direction: column !important;
      overflow: hidden !important;
      isolation: isolate !important;
    }
    ```

- [ ] **Clean Up Scroll and Navigation Classes**
  - Confirm `.bottom-nav` has `flex-shrink: 0 !important;` and has no fixed positioning constraints.
  - Ensure main scroll area (`main` inside `App.tsx` or `.content-area`) is styled to handle scroll locally:
    ```css
    main {
      flex: 1 !important;
      overflow-y: auto !important;
      -webkit-overflow-scrolling: touch !important;
    }
    ```

- [ ] **Refactor background mesh structure**
  - Edit `frontend/src/App.tsx` to move the three absolute mesh divs into a separate fixed wrapper:
    ```tsx
    {/* Fixed Isolated Background Mesh */}
    <div className="fixed inset-0 overflow-hidden pointer-events-none -z-10">
      <div className="absolute top-[-100px] left-[-100px] w-[500px] h-[500px] bg-sky-500/15 rounded-full blur-[120px]"></div>
      <div className="absolute bottom-[-50px] right-[-50px] w-[400px] h-[400px] bg-fuchsia-600/10 rounded-full blur-[100px]"></div>
      <div className="absolute top-[200px] right-[100px] w-[300px] h-[300px] bg-blue-500/10 rounded-full blur-[80px]"></div>
    </div>
    ```
  - Place this wrapper inside the `TonConnectUIProvider` but outside the `.app-container` to separate it from the UI layout.

- [ ] **Verify layout and build**
  - Run `npm run build` to verify there are no TypeScript or compilation errors.
  - Check in mobile emulator (Chrome DevTools responsive mode) for:
    - Zero horizontal scrolling (no empty space to the right).
    - Bottom menu positioned strictly at the bottom of the simulated mobile screen, keeping visible at all times.

---

## QA Scenarios

### Scenario 1: Desktop Browser Responsive Check
- Command: `npm run dev` in `frontend/`
- Action: Open `http://localhost:5173/` in a browser, open Developer Tools, choose mobile viewport (e.g., iPhone SE/12 Pro).
- Evidence: Scroll vertically inside the views. The header and bottom navigation must remain static. Swiping left/right should not scroll the viewport horizontally.

### Scenario 2: Telegram Mobile / Webview Check
- Action: Deploy and load inside Telegram.
- Evidence: Bottom menu should not require scrolling down. It must sit at the bottom edge of the webview above the Telegram bar.

---

## Privacy/Package Safeguards
- No private key details or KMS keys are exposed.
- All styles are standard CSS and compatible with Tailwind v4.

---

Next: `start-work tma_layout_fixes`
