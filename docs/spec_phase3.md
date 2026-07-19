# Phase 3 仕様: 通知（Bluesky）

## 目的
- Phase 2 の差分検知結果を使って、在庫復活時に通知する。
- 通知アダプタは Bluesky（AT Protocol）を採用する。当初はTelegram Bot APIを使用していたが、運用方針変更によりBlueskyへの投稿に切り替えた。
- 同一イベントの重複通知を抑止する。

## 入出力
### 入力
- 変更一覧（`detect_status_changes` の結果）
- 在庫復活イベント一覧（`detect_restock_events` の結果）
- Bluesky identifier（ハンドルまたはDID）/ app password（任意設定）
- 通知履歴ファイル（JSON）

### 出力
- Bluesky投稿（`app.bsky.feed.post` レコード）
- 送信済みイベント履歴（JSON）

## 認証・投稿フロー（AT Protocol）
1. `com.atproto.server.createSession` に identifier + app password をPOSTし、`accessJwt` / `did` を取得する。
2. 取得した `accessJwt` を `Authorization: Bearer` ヘッダに載せ、`com.atproto.repo.createRecord` に `repo=did`, `collection=app.bsky.feed.post`, `record={$type, text, createdAt}` をPOSTする。

`BlueskyNotifier`（`src/starbucks_monitor/notify.py`）がこのフローを実装する。

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

## 投稿文の制約
- Blueskyの投稿本文は最大300グラフェム程度の制約がある。
- `truncate_for_bluesky` で上限（`BLUESKY_MAX_GRAPHEMES = 300`）を超える場合は末尾を省略記号（`…`）で切り詰める。

## テスト観点
1. 通知メッセージが期待フォーマットになる。
2. Bluesky投稿が `createSession` → `createRecord` の順でAT ProtocolへPOSTされる。
3. `createRecord` が正しい `repo`（did）・`accessJwt`・投稿本文で呼ばれる。
4. 履歴により重複通知が抑止される。
5. 長文メッセージが投稿文字数上限で切り詰められる。

## テスト通知（運用確認用）
- `--send-test-notification` 指定時は、在庫変化が無くても現在ステータスの投稿を1回送る。
- 通知経路（identifier/app password）の疎通確認に使う。

## 運用上の必須条件（CI）
- GitHub Actions実行では、状態ファイル（`.starbucks_monitor_state.json`）と通知履歴ファイル（`.starbucks_monitor_notifications.json`）を実行間で永続化しないと「欠品→在庫あり」の遷移を検知できず、通知が発火しない。`.github/workflows/stock-monitor.yml` は実行後にこれらのファイルの変更をリポジトリへコミット＆プッシュすることで永続化している。
