# Live Stock Check (2026-02-23)

## Purpose
Verify whether the previous `403` access issue to Starbucks reward page is resolved, and confirm the current stock status for:

- スターマグ ブラウン 296ml
- スターマグ グリーン 296ml

## Results

1. Direct HTTP fetch from this environment now succeeds (no 403).
2. Existing CLI (`python -m starbucks_monitor.cli`) can access the page but returns `UNKNOWN` for both target products, because the static HTML contains both in-stock/out-of-stock button labels and the final state is switched by client-side JavaScript.
3. Browser-rendered DOM verification confirms both items are currently `在庫切れ` (out of stock):
   - `js-cartform-instock` button has `hide`
   - `js-cartform-outofstock` button is visible

## Raw command log

### Static CLI check
```bash
PYTHONPATH=src python -m starbucks_monitor.cli \
  --url "https://www.starbucks.co.jp/mystarbucks/reward/exchange/original_goods/" \
  --product "スターマグ ブラウン 296ml" \
  --product "スターマグ グリーン 296ml"
```

Output:

```text
2026-02-23T03:18:36	スターマグ ブラウン 296ml	UNKNOWN
2026-02-23T03:18:36	スターマグ グリーン 296ml	UNKNOWN
```

### Browser-rendered check (Playwright in browser tool)
Rendered DOM state:

- ブラウン: out-of-stock button visible (`在庫切れ`)
- グリーン: out-of-stock button visible (`在庫切れ`)

## Decision
- The connectivity blocker is resolved.
- For reliable live stock monitoring on this page, the monitor should include a browser-rendered mode (or equivalent JS-evaluated signal extraction), not static HTML-only parsing.


## Implementation update
- Added CLI `--mode rendered` and rendered-DOM parser to support JS-finalized stock state in Phase 1.
