# 銘柄リスト

## 現在の銘柄（Phase 1）

| ティッカー | 銘柄名 | 市場 | 通貨 |
|-----------|--------|------|------|
| 2327.T | 日鉄ソリューションズ | 東京 | JPY |
| 4528.T | 小野薬品工業 | 東京 | JPY |

---

## 追加予定銘柄

### インデックス（Phase 3）

| ティッカー | 名称 | 説明 | 通貨 |
|-----------|------|------|------|
| ^GSPC | S&P 500 | 米国株式市場の主要500社 | USD |

**代替候補**:
- `^IXIC` - NASDAQ Composite
- `^DJI` - Dow Jones Industrial Average
- `^NDX` - NASDAQ-100

---

### FANG+関連銘柄（Phase 4）

#### オプション1: 主要4銘柄（推奨）

| ティッカー | 銘柄名 | セクター | 時価総額 |
|-----------|--------|----------|----------|
| META | Meta Platforms | テクノロジー | ~$1.2T |
| AAPL | Apple | テクノロジー | ~$3.0T |
| AMZN | Amazon | 小売・クラウド | ~$1.7T |
| GOOGL | Alphabet (Google) | テクノロジー | ~$1.8T |

**理由**:
- 画面に収まる数
- FANG（Facebook, Amazon, Netflix, Google）の原型
- 高い流動性と知名度

#### オプション2: 拡張6銘柄

上記4銘柄 + 以下:

| ティッカー | 銘柄名 | セクター | 時価総額 |
|-----------|--------|----------|----------|
| NFLX | Netflix | エンターテイメント | ~$250B |
| NVDA | NVIDIA | 半導体 | ~$2.5T |

**理由**:
- NFLX: FANG の "N"
- NVDA: AI革命の中心企業

#### オプション3: フル8銘柄

上記6銘柄 + 以下:

| ティッカー | 銘柄名 | セクター | 時価総額 |
|-----------|--------|----------|----------|
| TSLA | Tesla | 自動車・エネルギー | ~$800B |
| MSFT | Microsoft | テクノロジー | ~$3.0T |

**理由**:
- TSLA: 電気自動車のリーダー
- MSFT: クラウド・AI分野で重要

**懸念**:
- 画面が混雑する可能性
- スクロールが必要になるかも

---

### 推奨構成（合計8銘柄）

#### 最終推奨: オプション2（拡張6銘柄）

**日本株（2銘柄）**:
1. 2327.T - 日鉄ソリューションズ
2. 4528.T - 小野薬品工業

**米国インデックス（1銘柄）**:
3. ^GSPC - S&P 500

**FANG+（6銘柄）**:
4. AAPL - Apple
5. MSFT - Microsoft
6. GOOGL - Alphabet
7. AMZN - Amazon
8. META - Meta
9. NVDA - NVIDIA

**合計: 9銘柄**

**レイアウト**:
- モバイル: 1列
- タブレット: 2列
- デスクトップ: 3列
- 大画面: 4列（オプション）

---

## その他の候補銘柄

### 米国テック大手（Magnificent 7）

| ティッカー | 銘柄名 | 備考 |
|-----------|--------|------|
| AAPL | Apple | ✓ 含める |
| MSFT | Microsoft | ✓ 含める |
| GOOGL | Alphabet | ✓ 含める |
| AMZN | Amazon | ✓ 含める |
| NVDA | NVIDIA | ✓ 含める |
| META | Meta | ✓ 含める |
| TSLA | Tesla | オプション |

### 日本株の追加候補

| ティッカー | 銘柄名 | セクター |
|-----------|--------|----------|
| 7203.T | トヨタ自動車 | 自動車 |
| 6758.T | ソニーグループ | 電機 |
| 9984.T | ソフトバンクグループ | 通信 |
| 6861.T | キーエンス | 電機 |
| 7974.T | 任天堂 | ゲーム |

---

## データソース情報

### yfinance ティッカーフォーマット

**日本株**:
- フォーマット: `{証券コード}.T`
- 例: `2327.T`, `7203.T`
- 市場: 東京証券取引所

**米国株**:
- フォーマット: `{ティッカー}`
- 例: `AAPL`, `MSFT`
- 市場: NYSE, NASDAQ

**米国インデックス**:
- フォーマット: `^{シンボル}`
- 例: `^GSPC`, `^IXIC`

**為替**:
- フォーマット: `{通貨1}{通貨2}=X`
- 例: `USDJPY=X`, `EURUSD=X`

---

## 実装時の設定

### app.py の STOCKS 辞書（最終形）

```python
STOCKS = {
    # 日本株
    "2327.T": {
        "name": "日鉄ソリューションズ",
        "currency": "JPY",
        "type": "stock",
        "category": "日本株"
    },
    "4528.T": {
        "name": "小野薬品工業",
        "currency": "JPY",
        "type": "stock",
        "category": "日本株"
    },

    # 米国インデックス
    "^GSPC": {
        "name": "S&P 500",
        "currency": "USD",
        "type": "index",
        "category": "インデックス"
    },

    # FANG+（米国テック株）
    "AAPL": {
        "name": "Apple",
        "currency": "USD",
        "type": "stock",
        "category": "FANG+"
    },
    "MSFT": {
        "name": "Microsoft",
        "currency": "USD",
        "type": "stock",
        "category": "FANG+"
    },
    "GOOGL": {
        "name": "Alphabet",
        "currency": "USD",
        "type": "stock",
        "category": "FANG+"
    },
    "AMZN": {
        "name": "Amazon",
        "currency": "USD",
        "type": "stock",
        "category": "FANG+"
    },
    "META": {
        "name": "Meta",
        "currency": "USD",
        "type": "stock",
        "category": "FANG+"
    },
    "NVDA": {
        "name": "NVIDIA",
        "currency": "USD",
        "type": "stock",
        "category": "FANG+"
    }
}
```

### カテゴリ別表示順序

1. **日本株** (2銘柄)
2. **米国インデックス** (1銘柄)
3. **FANG+** (6銘柄)

合計: **9銘柄**

---

## パフォーマンス考慮

### データ取得時間の見積もり

- 1銘柄あたり: ~500-1000ms（キャッシュミス時）
- 9銘柄逐次取得: ~4.5-9秒
- 9銘柄並列取得: ~1-2秒（推奨）

### 推奨: 並列取得の実装

```python
from concurrent.futures import ThreadPoolExecutor

def get_all_stocks_data() -> List[Dict]:
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(get_stock_data, STOCKS.keys()))
    return results
```

---

## 将来的な拡張

### Phase 10以降の候補

- **仮想通貨**: BTC-USD, ETH-USD
- **コモディティ**: 金 (GC=F), 原油 (CL=F)
- **その他インデックス**: NASDAQ (^IXIC), 日経平均 (^N225)
- **ユーザー設定**: カスタマイズ可能な銘柄リスト
