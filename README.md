# starbucks_reward_monitor_codex

スターバックス リワード交換ページの対象商品の在庫状況を監視するためのプロジェクト。

- 対象URL: `https://www.starbucks.co.jp/mystarbucks/reward/exchange/original_goods/`
- 対象商品（初期値）
  - スターマグ ブラウン 296ml
  - スターマグ グリーン 296ml

## 現在の状態
- Phase 0（計画策定）完了
- Phase 1 完了（static解析 + rendered解析 + CLIログ出力）
- Phase 2 完了（永続化・差分検知）
- Phase 3 着手（Telegram通知・重複通知抑止）

## 使い方（最小）
```bash
PYTHONPATH=src python -m starbucks_monitor.cli
```

任意の商品を指定する場合:
```bash
PYTHONPATH=src python -m starbucks_monitor.cli \
  --product "スターマグ ブラウン 296ml" \
  --product "スターマグ グリーン 296ml"
```

実ページの最終在庫状態（JS反映後）を取得する場合:
```bash
PYTHONPATH=src python -m starbucks_monitor.cli \
  --mode rendered \
  --product "スターマグ ブラウン 296ml" \
  --product "スターマグ グリーン 296ml"
```

> `--mode rendered` は Playwright が必要です。
> `pip install playwright && playwright install chromium`




差分検知+通知まで実行する場合（在庫復活時のみ通知）:
```bash
PYTHONPATH=src python -m starbucks_monitor.cli \
  --state-file .starbucks_monitor_state.json \
  --notification-history-file .starbucks_monitor_notifications.json \
  --telegram-bot-token "$TELEGRAM_BOT_TOKEN" \
  --telegram-chat-id "$TELEGRAM_CHAT_ID"
```

## テスト実行
```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

## ドキュメント
- 開発計画: `docs/development_plan.md`
- Phase 1仕様: `docs/spec_phase1.md`
- Phase 2仕様: `docs/spec_phase2.md`
- Phase 3仕様: `docs/spec_phase3.md`
- AIエージェント向け指示書: `docs/agent_handover_guide.md`

## Live stock verification note
- As of 2026-02-23, direct access to the Starbucks page from this environment is working again (403 resolved).
- This page finalizes stock button visibility via client-side JavaScript, so static HTML-only parsing can return `UNKNOWN`.
- See `docs/live_stock_check.md` for verification details and current observed status.

## GitHub Actions実行
- Workflow: `.github/workflows/stock-monitor.yml`
- 実行方式:
  - 手動実行（`workflow_dispatch`）
  - 30分おき定期実行（`schedule`）
- 必要Secrets:
  - `TELEGRAM_BOT_TOKEN`
  - `TELEGRAM_CHAT_ID`

