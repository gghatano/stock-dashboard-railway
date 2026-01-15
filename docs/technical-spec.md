# 技術仕様書

## 通貨表示機能の技術仕様

### 1. データモデルの拡張

#### 1.1 銘柄定義の変更

**変更前**:
```python
STOCKS = {
    "2327.T": "日鉄ソリューションズ",
    "4528.T": "小野薬品工業"
}
```

**変更後**:
```python
STOCKS = {
    "2327.T": {
        "name": "日鉄ソリューションズ",
        "currency": "JPY",
        "type": "stock"
    },
    "4528.T": {
        "name": "小野薬品工業",
        "currency": "JPY",
        "type": "stock"
    },
    "^GSPC": {
        "name": "S&P 500",
        "currency": "USD",
        "type": "index"
    },
    "META": {
        "name": "Meta Platforms",
        "currency": "USD",
        "type": "stock"
    },
    # 追加銘柄...
}
```

#### 1.2 株価データ構造

```python
{
    "ticker": str,              # ティッカーシンボル
    "name": str,                # 銘柄名
    "currency": str,            # "USD" or "JPY" (新規)
    "type": str,                # "stock" or "index" (新規)
    "current_price": float,     # 現在価格（元通貨）
    "change": float,            # 前日比（元通貨）
    "change_percent": float,    # 騰落率（%）
    "volume": int,              # 出来高
    "chart_data": List[dict],   # チャートデータ
    "last_update": str,         # 最終更新時刻
    "error": bool,              # エラー状態
    "error_message": str        # エラーメッセージ（エラー時のみ）
}
```

---

### 2. 為替レート取得

#### 2.1 関数仕様

```python
def get_exchange_rate() -> float:
    """
    ドル円の為替レートを取得（キャッシュ機能付き）

    Returns:
        float: ドル円レート（例: 147.52）
              エラー時は0.0を返す
    """
```

**実装詳細**:
- ティッカー: `USDJPY=X`
- キャッシュキー: `"USDJPY=X"`
- TTL: 30秒（`CACHE_TTL`と同じ）
- エラー時のフォールバック: 前回のキャッシュ値、または0.0

#### 2.2 キャッシュ構造

既存の`_cache`辞書を拡張:
```python
_cache = {
    "2327.T": (stock_data, timestamp),
    "4528.T": (stock_data, timestamp),
    "USDJPY=X": (exchange_rate_data, timestamp),  # 為替レート
    # ...
}
```

為替レートデータ構造:
```python
{
    "rate": 147.52,
    "last_update": "2026-01-15 22:00:00",
    "error": False
}
```

---

### 3. APIエンドポイント

#### 3.1 `/api/stocks` (変更)

**レスポンス**:
```json
{
    "stocks": [
        {
            "ticker": "2327.T",
            "name": "日鉄ソリューションズ",
            "currency": "JPY",
            "type": "stock",
            "current_price": 4560.0,
            "change": 63.0,
            "change_percent": 1.4,
            "volume": 204300,
            "chart_data": [...],
            "last_update": "2026-01-15 22:00:00",
            "error": false
        },
        {
            "ticker": "^GSPC",
            "name": "S&P 500",
            "currency": "USD",
            "type": "index",
            "current_price": 4783.23,
            "change": 15.50,
            "change_percent": 0.32,
            "volume": 0,
            "chart_data": [...],
            "last_update": "2026-01-15 22:00:00",
            "error": false
        }
    ],
    "exchange_rate": 147.52,
    "timestamp": "2026-01-15T22:00:00+09:00"
}
```

#### 3.2 `/api/exchange-rate` (新規・オプション)

**用途**: 為替レートのみを取得

**レスポンス**:
```json
{
    "rate": 147.52,
    "last_update": "2026-01-15 22:00:00",
    "timestamp": "2026-01-15T22:00:00+09:00"
}
```

---

### 4. フロントエンド実装

#### 4.1 通貨切り替えロジック

**JavaScriptでの実装例**:
```javascript
let currentCurrency = 'USD'; // or 'JPY'
let exchangeRate = 147.52;

function toggleCurrency() {
    currentCurrency = currentCurrency === 'USD' ? 'JPY' : 'USD';
    updateAllPrices();
    savePreference(); // localStorage
}

function convertPrice(price, fromCurrency, toCurrency) {
    if (fromCurrency === toCurrency) return price;
    if (fromCurrency === 'USD' && toCurrency === 'JPY') {
        return price * exchangeRate;
    }
    if (fromCurrency === 'JPY' && toCurrency === 'USD') {
        return price / exchangeRate;
    }
    return price;
}

function formatPrice(price, currency) {
    const symbol = currency === 'USD' ? '$' : '¥';
    const decimals = currency === 'USD' ? 2 : 0;
    return symbol + price.toLocaleString('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}
```

#### 4.2 トグルスイッチUI

**HTML**:
```html
<div class="flex items-center gap-2">
    <span class="text-sm text-gray-600">表示通貨:</span>
    <button id="currency-toggle"
            class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors"
            onclick="toggleCurrency()">
        <span class="sr-only">通貨切り替え</span>
        <span id="toggle-slider"
              class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform"></span>
    </button>
    <span id="currency-label" class="text-sm font-semibold">USD</span>
</div>
```

**CSS（Tailwindクラスで調整）**:
- USD時: 青背景、スライダー左寄せ
- JPY時: 緑背景、スライダー右寄せ

#### 4.3 データバインディング戦略

**オプションA: サーバーサイドレンダリング**
- サーバーで通貨換算を行い、HTMLを返す
- クエリパラメータ: `?currency=JPY`
- HTMX: `hx-vals='{"currency": "JPY"}'`

**オプションB: クライアントサイド計算**
- サーバーは元通貨のデータと為替レートを返す
- JavaScriptでリアルタイム換算
- ページリロードなしで切り替え可能

**推奨**: オプションB（クライアントサイド）
- 理由: UXが良い、サーバー負荷が少ない

---

### 5. 表示ルール

#### 5.1 通貨マーク

| 元通貨 | 表示通貨 | マーク | 例 |
|--------|----------|--------|-----|
| JPY | JPY | ¥ | ¥4,560 |
| JPY | USD | ¥ | ¥4,560 (変換不要) |
| USD | USD | $ | $4,783.23 |
| USD | JPY | ¥ | ¥705,891 |

#### 5.2 小数点以下の桁数

| 通貨 | 小数点桁数 | 理由 |
|------|-----------|------|
| USD | 2桁 | セント単位 |
| JPY | 0桁 | 円単位（銭は使わない） |

#### 5.3 換算計算式

**USD → JPY**:
```
円建て価格 = ドル建て価格 × ドル円レート
例: $4,783.23 × 147.52 = ¥705,891
```

**前日比の換算**:
```
円建て前日比 = ドル建て前日比 × ドル円レート
例: $15.50 × 147.52 = ¥2,287
```

**騰落率**:
```
騰落率は通貨に依存しない（%）
例: 0.32% はそのまま
```

#### 5.4 チャートデータの換算

```python
for point in chart_data:
    if display_currency == 'JPY' and stock['currency'] == 'USD':
        point['close_jpy'] = point['close'] * exchange_rate
```

---

### 6. エラーハンドリング

#### 6.1 為替レート取得失敗時

**フォールバック戦略**:
1. キャッシュに有効な過去データがあれば使用
2. なければデフォルト値を使用（例: 150.0）
3. UIに警告メッセージを表示

**実装例**:
```python
DEFAULT_EXCHANGE_RATE = 150.0

def get_exchange_rate() -> float:
    try:
        # 通常の取得処理
        ...
    except Exception as e:
        logger.error(f"Failed to get exchange rate: {e}")
        # キャッシュチェック
        if "USDJPY=X" in _cache:
            cached_data, _ = _cache["USDJPY=X"]
            return cached_data.get("rate", DEFAULT_EXCHANGE_RATE)
        return DEFAULT_EXCHANGE_RATE
```

#### 6.2 通貨換算エラー

**ゼロ除算対策**:
```python
def convert_to_jpy(usd_price: float, exchange_rate: float) -> float:
    if exchange_rate <= 0:
        logger.warning(f"Invalid exchange rate: {exchange_rate}")
        return 0.0
    return usd_price * exchange_rate
```

---

### 7. パフォーマンス最適化

#### 7.1 データ取得の並列化

現在は逐次取得:
```python
for ticker in STOCKS.keys():
    data = get_stock_data(ticker)
```

最適化案（ThreadPoolExecutor）:
```python
from concurrent.futures import ThreadPoolExecutor

def get_all_stocks_data_parallel() -> List[Dict]:
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(get_stock_data, ticker): ticker
                   for ticker in STOCKS.keys()}
        results = []
        for future in futures:
            results.append(future.result())
    return results
```

**注意**: スレッドセーフティは既に実装済み（`_cache_lock`）

#### 7.2 キャッシュヒット率の向上

- 為替レートは全米国株で共有
- 1回の取得で全リクエストに対応

---

### 8. セキュリティ考慮事項

#### 8.1 入力検証

**通貨パラメータ**:
```python
ALLOWED_CURRENCIES = {'USD', 'JPY'}

def validate_currency(currency: str) -> str:
    if currency.upper() not in ALLOWED_CURRENCIES:
        return 'USD'  # デフォルト
    return currency.upper()
```

#### 8.2 XSS対策

- Jinja2のオートエスケープは有効（デフォルト）
- ユーザー入力は受け付けない（表示のみ）

---

### 9. テストケース

#### 9.1 単体テスト

```python
def test_exchange_rate_retrieval():
    """為替レート取得のテスト"""
    rate = get_exchange_rate()
    assert rate > 0
    assert 100 < rate < 200  # 妥当な範囲

def test_currency_conversion():
    """通貨換算のテスト"""
    usd_price = 100.0
    exchange_rate = 150.0
    jpy_price = convert_to_jpy(usd_price, exchange_rate)
    assert jpy_price == 15000.0

def test_usd_stock_data():
    """USD銘柄のデータ取得テスト"""
    data = get_stock_data('^GSPC')
    assert data['currency'] == 'USD'
    assert data['type'] == 'index'
```

#### 9.2 統合テスト

- [ ] 全銘柄のデータが正しく取得できる
- [ ] 為替レートが正しく適用される
- [ ] UI切り替えが正常に動作する
- [ ] キャッシュが正常に動作する

---

### 10. デプロイメント

#### 10.1 環境変数（不要）

- yfinanceは認証不要
- 追加の環境変数は不要

#### 10.2 依存パッケージ

既存の`requirements.txt`で対応可能:
- yfinance 1.0
- その他変更なし

#### 10.3 Railway設定

`railway.toml`の変更は不要

---

## 実装の優先順位

1. **High**: Phase 2-3（ドル円レート、S&P500）
2. **Medium**: Phase 4-5（FANG+、円建て換算）
3. **Medium**: Phase 6（UI切り替え）
4. **Low**: Phase 7-9（最適化、テスト、ドキュメント）

---

## 参考情報

### yfinanceティッカーシンボル

| 種類 | シンボル | 説明 |
|------|---------|------|
| 日本株 | XXXX.T | 東京証券取引所 |
| 米国株 | XXXX | ティッカーシンボル |
| 米国インデックス | ^XXXX | ^付き |
| 為替 | XXXYYY=X | 通貨ペア |

### 主要インデックス

- S&P 500: `^GSPC`
- NASDAQ Composite: `^IXIC`
- Dow Jones: `^DJI`
- NASDAQ-100: `^NDX`
