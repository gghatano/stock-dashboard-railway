# CLAUDE.md

このファイルは、Claude Code (claude.ai/code) がこのリポジトリで作業する際のガイダンスを提供します。

## プロジェクト概要

FastAPIとHTMXで構築された日本株（日鉄ソリューションズ 2327.T、小野薬品工業 4528.T）のリアルタイム株価ダッシュボード。自動更新価格、5日間の価格チャート、出来高データ、メモリベースのキャッシュシステムを備えています。

## 開発コマンド

### アプリケーションの実行

```bash
# 依存パッケージのインストール
pip install -r requirements.txt

# ローカル実行（開発環境）
python app.py

# http://localhost:8000 でアクセス
```

### テスト

```bash
# ユニットテストの実行
pytest test_app.py -v

# カバレッジ付きで実行
pytest test_app.py -v --cov=app
```

### デプロイ

アプリケーションは`railway.toml`を通じてRailwayデプロイ用に構成されています。Railwayは自動的に`PORT`環境変数を使用します。

## アーキテクチャ

### コアアプリケーション (`app.py`)

**エントリポイント**: メインのFastAPIアプリケーション。`python app.py`で実行するか、Railwayの起動コマンドを使用します。

**スレッドセーフなキャッシュシステム**:
- `threading.Lock`を使用して並行リクエスト間のキャッシュアクセスを保護
- 2段階TTL: 通常データは30秒、エラーデータは10秒
- キャッシュ構造: `{ticker: (data_dict, timestamp)}`
- **重要**: `is_cache_valid()`は独自にロックを取得するため、呼び出し時に`_cache_lock`を保持してはいけません（デッドロック防止）

**データフロー**:
1. リクエスト → `get_all_stocks_data()` → 各銘柄に対して`get_stock_data(ticker)`
2. `get_stock_data()`は`is_cache_valid()`でキャッシュをチェック
3. キャッシュミス時: yfinanceから取得 → データ検証 → キャッシュに保存
4. データ辞書を返す（`None`は返さず、常にエラー状態を含む）

**NaN処理**:
- 価格データ: `current_price`と`prev_price`に対して`math.isnan()`チェック → 無効な場合はエラーデータを返す
- チャートデータ: ループ内でNaN値をスキップし、有効なデータポイントのみ追加
- 出来高データ: NaNを0に変換

**エラーハンドリング**:
- すべてのエラーは`create_error_data()`を介して構造化されたエラーデータになる
- エラーデータは短いTTLでキャッシュされ、API負荷を防止
- UIはエラー状態を破綻せずに適切に表示

### APIエンドポイント

- `GET /` - メインダッシュボード（HTMLを返す）
- `GET /api/stocks` - 全銘柄の株価データ（JSON形式）
- `GET /api/stocks/partial` - HTMX部分更新用（HTMLフラグメントを返す）
- `GET /health` - キャッシュ状態を含むヘルスチェック
- `GET /api/cache/clear` - キャッシュクリア（デバッグ用）

### フロントエンド (`templates/`)

- `index.html` - HTMXポーリング（`every 30s`）を含むメインページ
- `stocks_partial.html` - HTMX置換用の部分テンプレート
- スタイリングにTailwind CSS、リアクティブ更新にHTMXを使用
- 即座の更新のための手動更新ボタンあり

### 時刻処理

すべてのタイムスタンプはJST（日本標準時、`Asia/Tokyo`タイムゾーン）を使用します。`get_jst_now()`関数がアプリ全体で一貫性を保証します。

### 銘柄設定

ティッカーを追加/削除するには、`app.py`の`STOCKS`辞書を変更します:

```python
STOCKS = {
    "2327.T": "日鉄ソリューションズ",
    "4528.T": "小野薬品工業"
}
```

注意: 東京証券取引所のティッカー形式（`.T`サフィックス）を使用してください

### テストインフラストラクチャ (`test_app.py`)

yfinance API呼び出しのモックを使用したpytestを使用。テスト対象:
- キャッシュ検証ロジック
- スレッドセーフティ
- NaN処理
- エラー状態
- 並行アクセスパターン

キャッシュロジックを変更する際は、スレッドセーフティテストが引き続きパスすることを確認してください。

## 重要な実装ノート

1. **`get_stock_data()`から`None`を返さない** - 常にエラー状態を含む辞書を返す
2. **TOCTOUバグを避ける** - キャッシュの有効性チェックとキャッシュ取得を分離しない
3. **JST一貫性を維持** - すべてのタイムスタンプは`get_jst_now()`を使用する
4. **数値データを検証** - 算術演算前にNaNをチェックする
5. **ロックの規律** - クリティカルセクションを最小化し、ロック取得をネストしない

## よくある落とし穴

- `_cache_lock`を保持せずに`_cache`を変更しない
- yfinanceデータが常に有効だと仮定しない - 空のDataFrameとNaN値をチェックする
- API レート制限を考慮せずにキャッシュTTLを変更しない
- Railwayは`PORT`環境変数を必要とする - 本番環境設定でポート8000をハードコードしない

## トラブルシューティング

### yfinanceでデータが取得できない場合

**症状**: `Failed to get ticker reason: Expecting value: line 1 column 1 (char 0)`

**原因**: yfinanceのバージョンが古く、Yahoo Finance APIの変更に対応していない

**解決策**:
```bash
# yfinanceを最新版にアップグレード
uv pip install --upgrade yfinance

# requirements.txtとpyproject.tomlのバージョンを更新
# yfinance==1.0 以上を使用すること
```

**推奨バージョン**: yfinance 1.0以上（2026年1月時点）
