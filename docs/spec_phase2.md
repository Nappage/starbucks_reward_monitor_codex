# Phase 2 仕様: 永続化と差分検知

## 目的
- 前回実行時の在庫状態をローカルに保存する。
- 今回結果との差分を検知し、状態変化のみ抽出する。
- 特に `OUT_OF_STOCK -> IN_STOCK` を在庫復活イベントとして検知する。

## 入出力
### 入力
- 前回状態ファイルパス（JSON）
- 今回の監視結果（`run_monitor` の records）

### 出力
- 変更一覧（product / previous_status / current_status）
- 在庫復活イベント一覧（変更一覧のフィルタ）
- 更新後の状態JSON

## データ形式
```json
{
  "statuses": {
    "スターマグ ブラウン 296ml": "OUT_OF_STOCK",
    "スターマグ グリーン 296ml": "IN_STOCK"
  }
}
```

## ルール
1. 状態ファイルがなければ空状態として扱う。
2. `previous_status != current_status` の商品を変更として記録する。
3. `OUT_OF_STOCK -> IN_STOCK` のみ在庫復活イベントとする。

## テスト観点
1. ファイル未作成時に空状態を返す。
2. 保存→読み込みのroundtripが成立する。
3. 差分検知と在庫復活フィルタが正しく動く。
