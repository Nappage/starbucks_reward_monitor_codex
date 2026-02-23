# Phase 3 仕様: 通知（Telegram）

## 目的
- Phase 2 の差分検知結果を使って、在庫復活時に通知する。
- 初期アダプタは Telegram Bot API を採用する（メールより実装が簡単なため）。
- 同一イベントの重複通知を抑止する。

## 入出力
### 入力
- 変更一覧（`detect_status_changes` の結果）
- 在庫復活イベント一覧（`detect_restock_events` の結果）
- Telegram bot token / chat id（任意設定）
- 通知履歴ファイル（JSON）

### 出力
- Telegram 送信メッセージ
- 送信済みイベント履歴（JSON）

## 通知条件
1. `OUT_OF_STOCK -> IN_STOCK` のイベントがある場合のみ通知対象。
2. 同一イベントID（`product|previous_status|current_status`）が履歴に存在する場合は送信しない。

## データ形式
```json
{
  "sent_event_ids": [
    "スターマグ ブラウン 296ml|OUT_OF_STOCK|IN_STOCK"
  ]
}
```

## テスト観点
1. 通知メッセージが期待フォーマットになる。
2. Telegram送信がBot APIへのPOSTで行われる。
3. 履歴により重複通知が抑止される。


## テスト通知（運用確認用）
- `--send-test-notification` 指定時は、在庫変化が無くても現在ステータスの通知を1回送る。
- 通知経路（Bot token/chat id）の疎通確認に使う。
