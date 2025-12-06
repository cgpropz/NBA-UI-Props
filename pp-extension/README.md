# CGEDGE PrizePicks Autofill Extension

This Chrome extension auto-fills your PrizePicks slip directly on the PrizePicks website using the `ppSlip` saved by the CGEDGE dashboard.

## How it works
- On `https://www.prizepicks.com`, the extension reads `localStorage.ppSlip` which the dashboard writes when you click “Open PrizePicks”.
- It attempts to select the correct prop tab (Points, Rebounds, etc.), locate the player card, and click to add the pick (defaults to Over).
- It runs shortly after page load and iterates through all items in the slip.

## Install (Developer mode)
1. Open Chrome and go to `chrome://extensions`.
2. Enable “Developer mode” (top right).
3. Click “Load unpacked” and select the folder `pp-extension` in your repo.
4. Ensure the extension is enabled.

## Usage
1. On the CGEDGE dashboard (`index.html`), build your slip.
2. Click “Review Slip” then “Open PrizePicks” — this saves `ppSlip` to localStorage and opens `https://www.prizepicks.com`.
3. On the PrizePicks tab, the extension will attempt to auto-add each pick. You can adjust picks or choose Under manually if needed.

## Notes & Limitations
- PrizePicks DOM can change; the extension uses heuristics to find tabs and player cards. If something breaks, update `content.js` selectors.
- Exact line matching isn’t guaranteed; PP sometimes shows dynamic lines. The extension focuses on selecting the correct player and prop category.
- This is client-side only and uses your authenticated PrizePicks session in the browser; it does not store credentials nor call private APIs.

## Uninstall
- Remove the extension in `chrome://extensions` or disable it.

