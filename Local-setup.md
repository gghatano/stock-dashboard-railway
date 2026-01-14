# ローカル環境での実行手順

## 📋 前提条件

- Python 3.8以上がインストールされていること
- インターネット接続があること（yfinanceがデータを取得するため）

## 🚀 実行手順

### 1. プロジェクトの展開

ダウンロードした `stock-dashboard-v1.3.0.tar.gz` を展開します。

```bash
# Macの場合
tar -xzf stock-dashboard-v1.3.0.tar.gz
cd stock-dashboard

# Windowsの場合（PowerShell）
tar -xzf stock-dashboard-v1.3.0.tar.gz
cd stock-dashboard
```

### 2. 仮想環境の作成（推奨）

プロジェクト専用の仮想環境を作成します。

```bash
# Macの場合
python3 -m venv venv
source venv/bin/activate

# Windowsの場合（PowerShell）
python -m venv venv
.\venv\Scripts\Activate.ps1

# Windowsの場合（コマンドプロンプト）
python -m venv venv
venv\Scripts\activate.bat
```

仮想環境が有効化されると、プロンプトの先頭に `(venv)` が表示されます。

### 3. 依存パッケージのインストール

```bash
# 依存パッケージをインストール
pip install -r requirements.txt
```

インストールされるパッケージ：
- fastapi==0.109.0
- uvicorn[standard]==0.27.0
- jinja2==3.1.3
- yfinance==0.2.36
- python-multipart==0.0.6
- pytz==2024.1

### 4. アプリケーションの起動

```bash
# 方法1: Pythonで直接実行
python app.py

# 方法2: uvicornコマンドで実行
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

**オプション説明:**
- `--host 0.0.0.0`: すべてのネットワークインターフェースでリッスン
- `--port 8000`: ポート8000で起動
- `--reload`: コード変更時に自動リロード（開発時に便利）

### 5. ブラウザでアクセス

アプリケーションが起動したら、以下のURLにアクセスします。

```
http://localhost:8000
```

または

```
http://127.0.0.1:8000
```

### 6. 動作確認

以下のエンドポイントで動作を確認できます：

- **メインページ**: http://localhost:8000
- **APIエンドポイント**: http://localhost:8000/api/stocks
- **ヘルスチェック**: http://localhost:8000/health
- **API仕様書**: http://localhost:8000/docs

## 🛑 アプリケーションの停止

ターミナルで `Ctrl + C` を押すと、アプリケーションが停止します。

## 🔍 トラブルシューティング

### ポートが既に使用されている場合

```bash
# エラー: Address already in use
# 別のポートで起動
python app.py  # app.pyは環境変数PORTを読むので以下のように指定
# または
PORT=8001 python app.py  # Mac/Linux
$env:PORT=8001; python app.py  # Windows PowerShell

# または直接uvicornで別ポート指定
uvicorn app:app --host 0.0.0.0 --port 8001
```

### yfinanceのデータ取得エラー

```
# エラー: No historical data found
# 原因: 市場が休場、またはティッカーシンボルが無効

対処法:
1. 東京証券取引所の営業時間を確認
2. インターネット接続を確認
3. しばらく待ってから再度アクセス
```

### Pythonバージョンエラー

```bash
# Python 3.8以上が必要
python --version  # バージョン確認

# Python 3.8未満の場合はアップグレード
# Macの場合
brew install python@3.11

# Windowsの場合
# https://www.python.org/ から最新版をダウンロード
```

### 依存パッケージのインストールエラー

```bash
# pipを最新版にアップグレード
pip install --upgrade pip

# 再度インストール
pip install -r requirements.txt
```

## 📊 ログの確認

アプリケーションを起動すると、以下のようなログが表示されます：

```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

データ取得時のログ：

```
2026-01-14 15:00:00 - __main__ - INFO - Fetching fresh data for 2327.T
2026-01-14 15:00:01 - __main__ - INFO - Fetching fresh data for 4528.T
```

キャッシュヒット時のログ：

```
2026-01-14 15:00:15 - __main__ - INFO - Using cached data for 2327.T
2026-01-14 15:00:15 - __main__ - INFO - Using cached data for 4528.T
```

## 🎨 開発モードでの起動

コードを変更しながら開発する場合は、`--reload` オプションを使用します：

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

これにより、ファイルを保存するたびに自動的にアプリケーションが再起動します。

## 🧪 動作テスト

### 1. 基本動作確認

ブラウザで http://localhost:8000 にアクセスし、以下を確認：
- 2つの銘柄カードが表示される
- 価格、前日比、出来高が表示される
- チャートが表示される

### 2. 自動更新の確認

ページを開いたまま30秒以上待つと、データが自動更新されます。

### 3. 手動更新の確認

「手動更新」ボタンをクリックすると、即座にデータが更新されます。

### 4. APIレスポンスの確認

```bash
# JSONレスポンスを確認
curl http://localhost:8000/api/stocks

# ヘルスチェック
curl http://localhost:8000/health
```

### 5. キャッシュの確認

1. 初回アクセス（キャッシュミス）
2. 30秒以内に再アクセス（キャッシュヒット）
3. ログでキャッシュの動作を確認

## 📝 設定のカスタマイズ

### 監視銘柄の変更

`app.py` の24-27行目を編集：

```python
STOCKS = {
    "7203.T": "トヨタ自動車",
    "6758.T": "ソニーグループ",
    # 追加したい銘柄...
}
```

### キャッシュTTLの変更

`app.py` の34-35行目を編集：

```python
CACHE_TTL = 30  # 通常データのキャッシュ時間（秒）
ERROR_CACHE_TTL = 10  # エラーデータのキャッシュ時間（秒）
```

### 自動更新間隔の変更

`templates/index.html` の43行目を編集：

```html
hx-trigger="every 30s"  <!-- 秒単位で指定 -->
```

## 🌐 ネットワーク内の他のデバイスからアクセス

同じネットワーク内の他のデバイスからアクセスする場合：

1. 起動したPCのIPアドレスを確認

```bash
# Mac/Linux
ifconfig | grep inet

# Windows
ipconfig
```

2. 他のデバイスのブラウザで以下にアクセス

```
http://<起動したPCのIPアドレス>:8000
```

例: `http://192.168.1.100:8000`

## 🔧 よくある質問

### Q: データが表示されない
A: 以下を確認してください：
- インターネット接続
- 東京証券取引所の営業時間（平日9:00-15:00）
- ログにエラーが出ていないか

### Q: 更新が遅い
A: yfinanceがデータを取得するのに時間がかかることがあります（500-1000ms）。キャッシュが効いていれば2回目以降は高速です。

### Q: エラー画面が表示される
A: 以下の可能性があります：
- 市場が休場中
- 銘柄コードが無効
- yfinanceのAPIに問題がある

ログを確認してエラー内容を特定してください。

## 📚 参考情報

- FastAPI公式ドキュメント: https://fastapi.tiangolo.com/
- yfinance GitHub: https://github.com/ranaroussi/yfinance
- HTMX公式サイト: https://htmx.org/
- TailwindCSS公式サイト: https://tailwindcss.com/

## 🎯 次のステップ

ローカルで動作確認できたら、Railwayへのデプロイを試してみましょう！
デプロイ手順は README.md の「Railwayへのデプロイ」セクションを参照してください。
