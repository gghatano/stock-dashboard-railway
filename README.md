# 株価ダッシュボード

日鉄ソリューションズ(2327.T)と小野薬品工業(4528.T)の株価をリアルタイムで表示するダッシュボードアプリケーション。

## 機能

- 現在の株価表示
- 前日比・騰落率の表示
- 出来高情報
- 直近5日間の価格推移チャート
- 30秒ごとの自動更新（HTMX polling）
- **キャッシュ機構**（30秒間のデータキャッシュでAPI呼び出しを削減）
- **エラーハンドリング**（データ取得失敗時の適切な表示）
- **ヘルスチェックエンドポイント**（Railway監視用）
- **構造化ロギング**（デバッグとモニタリング用）
- **JST（日本標準時）対応**

## 技術スタック

- **Backend**: FastAPI
- **Frontend**: HTMX + TailwindCSS
- **Data Source**: yfinance (Yahoo Finance API)
- **Timezone**: pytz (日本時間対応)

## アーキテクチャの特徴

### キャッシュ機構
- メモリベースの簡易キャッシュ（Redis不要）
- 30秒間のTTL（Time To Live）
- yfinance APIへの過度なリクエストを防止

### エラーハンドリング
- データ取得失敗時のフォールバック表示
- 構造化ログによる詳細なエラー追跡
- ユーザーフレンドリーなエラーメッセージ

### コード品質
- DRY原則に基づいたコード重複の排除
- 型ヒント（Type Hints）の使用
- 適切なロギングレベル

## ローカル実行

```bash
# 依存パッケージのインストール
pip install -r requirements.txt

# アプリケーションの起動
python app.py
```

ブラウザで `http://localhost:8000` にアクセス

## Railwayへのデプロイ

1. GitHubリポジトリを作成してコードをpush
2. [Railway](https://railway.app/)にログイン
3. "New Project" → "Deploy from GitHub repo"
4. リポジトリを選択
5. 自動的にデプロイが開始されます

### 環境変数

特に設定不要（yfinanceは認証不要のため）

### ポート設定

Railwayは自動的に`$PORT`環境変数を設定します。
`railway.toml`で`--port $PORT`を指定しているため、追加設定は不要です。

## API エンドポイント

### `GET /`
メインダッシュボード画面

### `GET /api/stocks`
全銘柄の株価データ（JSON形式）
```json
{
  "stocks": [...],
  "timestamp": "2026-01-14T10:30:00+09:00"
}
```

### `GET /api/stocks/partial`
HTMX用の部分更新HTML

### `GET /health`
ヘルスチェックエンドポイント
```json
{
  "status": "healthy",
  "timestamp": "2026-01-14T10:30:00+09:00",
  "cache_size": 2
}
```

### `GET /api/cache/clear`
キャッシュクリア（デバッグ用）

## 注意事項

- データは東京証券取引所の営業時間外は前営業日の終値が表示されます
- yfinanceは無料で使えますが、データの精度や遅延については保証されません
- キャッシュTTLは30秒に設定されており、頻繁なリクエストでもAPI呼び出しは最小限に抑えられます

## ファイル構成

```
stock-dashboard/
├── app.py                      # FastAPIアプリケーション
├── templates/
│   ├── index.html             # メインページ
│   └── stocks_partial.html    # 部分更新用テンプレート
├── requirements.txt           # Python依存パッケージ
├── railway.toml              # Railway設定
├── .gitignore                # Git除外設定
└── README.md                 # このファイル
```

## カスタマイズ

### 監視銘柄の変更

`app.py`の`STOCKS`辞書を編集：

```python
STOCKS = {
    "7203.T": "トヨタ自動車",
    "6758.T": "ソニーグループ",
    # 追加したい銘柄...
}
```

### 更新間隔の変更

`templates/index.html`の`hx-trigger`属性を編集：

```html
hx-trigger="every 30s"  <!-- 30秒ごと -->
```

### キャッシュTTLの変更

`app.py`の`CACHE_TTL`定数を編集：

```python
CACHE_TTL = 30  # 秒単位
```

## 改善履歴

### v1.3.0 (Latest) - 堅牢性強化版
- ✅ **is_cache_valid()の完全スレッドセーフ化**: TOCTOU問題を解決、二重ロック解消
- ✅ **価格データのNaNチェック**: 不正な価格データを早期検出してエラー表示
- ✅ **チャートデータのNaNフィルタリング**: 無効なデータポイントをスキップ
- ✅ **ログレベルの適正化**: データなし時はwarning、システムエラー時はerror

### v1.2.0 - 本番環境対応版
- ✅ **スレッドセーフティの実装**: `threading.Lock`でキャッシュへのアクセスを保護（複数リクエスト対応）
- ✅ **エラーハンドリングの統一**: `get_stock_data()`は常にDictを返す（`None`を返さない）
- ✅ **タイムスタンプの一貫性**: 同じタイムスタンプをデータとキャッシュで使用
- ✅ **エラーキャッシング**: エラー時も短いTTL（10秒）でキャッシュして連続エラーのAPI負荷を軽減
- ✅ **NaN値の処理**: 出来高がNaNの場合は0を返す
- ✅ **Railway環境対応**: `PORT`環境変数の読み取り
- ✅ **未使用インポートの完全削除**: `JSONResponse`, `timezone`, `timedelta`, `lru_cache`, `Optional`を削除
- ✅ **`create_error_data()`ヘルパー関数**: エラーデータ生成の共通化

### v1.1.0
- ✅ 未使用インポートの削除
- ✅ メモリベースのキャッシュ機構追加
- ✅ 構造化ロギングの実装
- ✅ コード重複の排除
- ✅ エラーハンドリングの改善
- ✅ ヘルスチェックエンドポイント追加
- ✅ JST（日本標準時）対応
- ✅ 型ヒントの追加
- ✅ 手動更新ボタンの追加

### v1.0.0
- 🎉 初回リリース

## パフォーマンス

- **キャッシュヒット時**: <10ms
- **キャッシュミス時**: ~500-1000ms（yfinance API呼び出し含む）
- **メモリ使用量**: <50MB（通常運用時）

## ライセンス

MIT
