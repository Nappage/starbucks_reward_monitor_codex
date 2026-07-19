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
- Phase 3 完了（Bluesky通知・重複通知抑止）

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




差分検知+通知まで実行する場合（在庫復活時のみBlueskyへ投稿）:
```bash
PYTHONPATH=src python -m starbucks_monitor.cli \
  --state-file .starbucks_monitor_state.json \
  --notification-history-file .starbucks_monitor_notifications.json \
  --bluesky-identifier "$BLUESKY_IDENTIFIER" \
  --bluesky-app-password "$BLUESKY_APP_PASSWORD"
```

テスト投稿を明示的に送る（在庫変化がなくても1回投稿）:
```bash
PYTHONPATH=src python -m starbucks_monitor.cli \
  --mode rendered \
  --send-test-notification \
  --bluesky-identifier "$BLUESKY_IDENTIFIER" \
  --bluesky-app-password "$BLUESKY_APP_PASSWORD"
```

> Bluesky通知には、アプリパスワード（Bluesky設定画面の「App Passwords」で発行するもの。通常のログインパスワードではない）が必要です。
> `--bluesky-identifier` にはハンドル（例: `example.bsky.social`）またはDIDを指定します。


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
- 実行後、状態ファイル（`.starbucks_monitor_state.json` / `.starbucks_monitor_notifications.json`）に変更があれば自動でリポジトリへコミット＆プッシュし、次回実行に引き継ぐ（差分検知に必須）。

- テスト投稿（在庫変化がなくてもBlueskyへの送信経路を確認）:
  - Actions手動実行時に `send_test_notification=true` を指定
- 必要Secrets:
  - `BLUESKY_IDENTIFIER`（ハンドルまたはDID）
  - `BLUESKY_APP_PASSWORD`（Bluesky設定画面で発行するアプリパスワード）

### 定期実行の自動停止に関する注意
GitHub Actionsは、リポジトリに60日間コミット等のアクティビティが無いと `schedule` トリガーを自動的に無効化する。これを防ぐため、`.github/workflows/keepalive.yml` が毎月1日・15日にハートビート用の空コミットを行い、定期実行が止まらないようにしている。
- もし在庫監視が動いていない場合は、GitHubのActionsタブで `Starbucks stock monitor` ワークフローが `disabled_inactivity` 状態になっていないか確認し、無効化されていれば手動で「Enable workflow」を実行すること（API単独では再有効化できないため、UIまたは適切な権限のトークンでの操作が必要）。

