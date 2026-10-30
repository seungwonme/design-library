# Verification record

## Code and data

- `node --check preview-camera-framing.js` passed.
- `node --check app.js` passed.
- `camera-map-framing.json` parsed successfully.
- Contract check passed: 33 unique item IDs, 33 unique `framing:` preview IDs, every entry `motion:false`, and every renderer ID present.
- Node VM renderer smoke passed for all 33 `sample()` and `draw()` calls.
- Local HTTP smoke passed for `index.html` and the mapping JSON.

## Live screen

The public Pages URL was opened in Chromium at 1440x1000. The first deployment exposed a real integration bug: the renderer expected a context while the app passed a canvas element. The fix was published as `908c020 fix(gallery): accept canvas preview targets`, and the Pages workflow completed successfully afterward.

The corrected live page rendered all 33 cards. The accessibility tree exposed the searchbox, filter buttons, theme toggle, Canvas labels, source links and redraw buttons. Selecting `광학/환경` showed 9 cards, dark mode toggled its pressed state and palette, and searching `망원` narrowed the result.

## Scope limits

The live check is a browser/Pages integration check, not a full WCAG audit, Safari test, physical-device test, optical simulation validation or pixel-identical reproduction assessment.
