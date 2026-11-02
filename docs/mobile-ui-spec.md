# Street CEO Mobile APK UI/UX Specification

**Status:** Ready for Capacitor implementation  
**Date:** 2026-10-30  
**Scope:** First Android APK screens and interaction contract  
**Implementation boundary:** This document only. It does not change `apps/web/` or Android source.

## 1. Product direction

Street CEO is a fast, calm operating tool for a small shop owner using a low-cost Android phone, often with one hand, bright sunlight, noise, and intermittent connectivity. The mobile app must make the next useful action obvious:

1. See how the shop is doing today.
2. Record a sale quickly by touch or Apo/Napo voice.
3. Check stock and upload a supplier invoice.
4. Ask for a source-backed profitability explanation.
5. See the team and delivery progress.

The APK wraps the existing React mobile-first experience with Capacitor. It is not a second product or a native rewrite.

## 2. Navigation

Use a persistent bottom navigation bar with five destinations:

| Tab | Purpose | Primary action |
|---|---|---|
| Today | Sales, stock alerts, insight, profitability entry | Record a sale |
| Sell | Basket, touch sale, Apo/Napo voice | Confirm sale |
| Stock | Catalogue, quantities, invoice upload | Upload invoice |
| Profit | Monthly and custom-period analysis | Ask Muse |
| Team | Delivery roadmap, owner/stage/progress filters | Open a feature |

The selected tab uses the brand green. Each tab keeps its state when switching tabs. Android back returns from a detail view to its parent tab; it does not exit the app until the user is at a root tab.

### Global top bar

- Left: real Street CEO logo, using `apps/web/public/street-ceo-logo.png` in the packaged asset bundle. Never replace it with an `SC` placeholder.
- Centre: current page title.
- Right: connectivity badge (`Online`, `Offline`, or `Syncing`) and an overflow menu for API settings/help.
- Keep the logo mark at 40–44 dp high with a minimum 12 dp safe area.

## 3. Design tokens

### Visual language

- Background: warm off-white `#F5F8F7`.
- Primary text: deep navy `#092640`.
- Brand green: `#0B9A8C` for primary actions and active navigation.
- Success: `#168A65`.
- Warning: `#A9691C` on pale cream.
- Error: `#B34A35` on pale coral.
- Cards: white with a 1 px cool-grey border and a soft 12–16 dp radius.
- Avoid gradients and dense dashboard chrome; the app should feel practical and trustworthy.

### Type and spacing

- Use the existing system/web font stack so the APK remains fast and readable.
- Page title: 28 sp, 700 weight, 32 sp line height.
- Section title: 20 sp, 700 weight, 24 sp line height.
- Body: 16 sp, 400 weight, 22 sp line height.
- Label/metadata: 12–14 sp, 500 weight, 18 sp line height.
- Monetary totals: 28–32 sp, 700 weight.
- Base spacing unit: 4 dp. Use 16 dp page gutters, 20 dp card padding, 12 dp between controls, and 24 dp between sections.
- Minimum touch target: 48 × 48 dp. Never rely on a tiny icon-only target.

## 4. Screen specifications

### 4.1 Today dashboard

Header: “Good morning, [shop owner]” and the current date. Show the selected currency explicitly.

Content order:

1. Today’s sales card: amount, transaction count, and comparison only when the API supplies a real prior-day value. Do not invent a percentage.
2. Stock alerts card: count and a link to Stock.
3. Primary CTA: `Record a sale`.
4. Street CEO insight card: short source-backed insight with “Why?” expansion showing the period and inputs used.
5. `Profitability analysis` card opening Profit.
6. Small sync/API state banner when offline, syncing, demo data, or the API is unavailable.

States:

- Loading: skeleton cards, not zeros.
- Empty: “No completed sales today yet” with `Record a sale`.
- Offline: show last synced timestamp and allow queued sale entry.
- API error: explain what is unavailable and preserve the user’s last successful data.

### 4.2 Sell — touch and Apo/Napo voice

The Sell screen is the fastest path and must open directly to the product search/basket.

Top:

- `What did you sell?`
- Search catalogue field with a large clear button.
- Basket total and item count, pinned above the bottom action area.

Product rows:

- Product name, SKU, available stock, unit price.
- Large minus, quantity, plus controls.
- Add button when quantity is zero.
- Clear insufficient-stock feedback before submission.

Voice panel:

- Label: `Apo / Napo voice`.
- Primary control: `Press and hold to talk`.
- Helper text: `Say Apo, list the sale, then say Napo.`
- Example: `Apo … 1 Coke, 2 sugar, 2 milk … Napo`.
- While listening: animated level indicator, elapsed seconds, and `Release to transcribe`.
- Transcript state: show the exact transcript and the interpreted items separately.
- Confirmation state: `Confirm sale` and `Edit basket`; no sale is posted before confirmation.
- Failure state: `Could not understand that. Try again or use the basket.` Never silently post.

Sale completion:

- Tender choice: Cash or Bank.
- Show final items, quantities, total, and stock impact.
- Submit button: `Confirm sale`.
- Success: receipt-style summary, new stock values, and `New sale`.
- Offline success: `Saved on this phone — will sync when online`, with a visible queue count.

### 4.3 Stock and invoice upload

Top segmented control: `Catalogue` and `Invoices`.

Catalogue:

- Search/filter products.
- Product card: name, SKU, quantity, unit price, low-stock state.
- Use clear badges: `In stock`, `Low stock`, `Out of stock`.

Invoices:

- Primary button: `Upload an invoice`.
- Accept PDF and image files; show file name, size, upload progress, and retry.
- After upload, show a review table: extracted product, quantity, unit cost, confidence, and matching catalogue item.
- Required safety copy: `Review before posting to stock.`
- Actions: `Save for review`, `Post receipt`, `Remove`.
- Current backend limitation must be represented honestly: if extraction is not available, show `Uploaded — line-item extraction pending` rather than implying stock changed.

### 4.4 Profitability

Header: `Profitability` with period selector: This month, Last month, Custom.

Question composer:

- Text field: `Ask about your sales or profit`.
- Microphone button with text fallback.
- Example chips: `What was my profit this month?`, `Which products make the most margin?`, `What should I restock?`.
- Submit: `Analyse`.

Result:

- Revenue, cost of goods, gross profit, and margin cards.
- Date range and currency beside every result.
- Short answer from Meta/Muse, followed by `Based on` inputs and assumptions.
- If costs or ledger data are incomplete, show an explicit confidence/limitation panel and do not present a guessed profit as fact.
- Empty state: explain that a completed sale and cost data are needed.

### 4.5 Team

The Team screen is a work tracker, not a decorative office scene. Default view is a readable list/table on a phone.

Controls:

- Feature filter: All, PostgreSQL, Ledger, Inventory, Web/PWA, Offline, Apo/Napo voice, Invoice intake, Sales analysis, Social updates.
- Owner filter: All, Hwaro, Verengai, Dura, Runako, Fambai, Inzwi, Ungwaru, Chiono, Chengetai, Mutungamiri, Ruzivo.
- Stage filter: Development, QA/evidence, Ready, Review/blocked.

Task card:

- Feature name and task ID.
- Owner(s), stage, percentage, and last verified evidence time.
- Progress bar with accessible text, e.g. `60% complete`.
- `Done` list and `To do next` list.
- Dependency/blocker text.
- Tap card to open detail; do not require a 3D room for basic status discovery.

Detail view:

- Description and acceptance criteria.
- Stage timeline: Development → QA/evidence → Ready.
- Files changed, commits, tests run/passing, and last handoff.
- Evidence timestamp and a clear `Repository evidence only` disclaimer.
- Never claim live typing, private agent thoughts, or a literal remote computer screen.

Optional room view can remain a visual overview, but it must link to the same task detail and never be the only way to understand progress.

## 5. APK and Capacitor implementation notes

- Build the existing web app first, then package its output with Capacitor.
- Keep the API base URL configurable for local development. For the local APK, use the PC LAN address, for example `http://192.168.10.213:8000`, not `localhost`.
- The debug APK may allow cleartext HTTP for local testing only. Release builds should use HTTPS or a controlled private network.
- Request microphone permission only when the user starts voice capture; explain why.
- Request file/media permission only when the user chooses an invoice or shop image.
- Use safe-area insets, Android back handling, keyboard resize behavior, and a bottom navigation height of at least 64 dp.
- Preserve offline sale capture and idempotency. A queued sale must show its state and never be duplicated on replay.
- Avoid storing Meta/Muse API keys in the APK. The app calls the backend boundary.

## 6. Acceptance checklist for the first mobile build

- [ ] Real Street CEO logo appears in the app bar, splash/icon assets, and does not fall back to `SC`.
- [ ] Five-tab navigation works with Android back behavior.
- [ ] Manual multi-item sale can be reviewed and confirmed.
- [ ] Apo/Napo shows listening, transcript, interpreted basket, confirmation, and safe failure states.
- [ ] Stock shows catalogue and invoice upload/review states.
- [ ] Profitability supports typed questions and a microphone entry point.
- [ ] Team supports feature, owner, and stage filters with readable task cards.
- [ ] Offline/sync/API error states are visible and non-destructive.
- [ ] APK can target a configurable local HTTP API in debug mode.
- [ ] No credentials are bundled in the APK.

