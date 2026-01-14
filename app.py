from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import yfinance as yf
from datetime import datetime
import uvicorn
import logging
from typing import Dict, List
from threading import Lock
import pytz
import os
import math

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Stock Dashboard", version="1.3.0")
templates = Jinja2Templates(directory="templates")

# 監視する銘柄
STOCKS = {
    "2327.T": "日鉄ソリューションズ",
    "4528.T": "小野薬品工業"
}

# 日本時間のタイムゾーン
JST = pytz.timezone('Asia/Tokyo')

# キャッシュの有効期限（秒）
CACHE_TTL = 30
ERROR_CACHE_TTL = 10  # エラー時は短めのキャッシュ

# キャッシュ用のグローバル変数とロック
_cache: Dict[str, tuple] = {}  # {ticker: (data, timestamp)}
_cache_lock = Lock()


def get_jst_now() -> datetime:
    """日本時間の現在時刻を取得"""
    return datetime.now(JST)


def is_cache_valid(ticker: str, now: datetime) -> bool:
    """
    キャッシュが有効かチェック（スレッドセーフ）
    
    Note: この関数内部でロックを取得するため、呼び出し側でロックを取る必要はない
    
    Args:
        ticker: ティッカーシンボル
        now: 現在時刻
        
    Returns:
        キャッシュが有効ならTrue
    """
    with _cache_lock:
        if ticker not in _cache:
            return False
        
        data, cached_time = _cache[ticker]
        elapsed = (now - cached_time).total_seconds()
        
        # エラーデータの場合は短いTTL、通常データは標準TTL
        ttl = ERROR_CACHE_TTL if data.get("error", False) else CACHE_TTL
        return elapsed < ttl


def create_error_data(ticker: str, error_message: str, timestamp_str: str) -> Dict:
    """
    エラー時のフォールバックデータを作成
    
    Args:
        ticker: ティッカーシンボル
        error_message: エラーメッセージ
        timestamp_str: タイムスタンプ文字列
        
    Returns:
        エラーデータの辞書
    """
    return {
        "ticker": ticker,
        "name": STOCKS.get(ticker, ticker),
        "current_price": 0,
        "change": 0,
        "change_percent": 0,
        "volume": 0,
        "chart_data": [],
        "last_update": timestamp_str,
        "error": True,
        "error_message": error_message
    }


def get_stock_data(ticker: str) -> Dict:
    """
    株価データを取得（キャッシュ機能付き）
    
    Args:
        ticker: ティッカーシンボル
        
    Returns:
        株価データの辞書（常にDictを返す、Noneは返さない）
    """
    now = get_jst_now()
    timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
    
    # スレッドセーフなキャッシュチェック
    if is_cache_valid(ticker, now):
        logger.info(f"Using cached data for {ticker}")
        with _cache_lock:
            data, _ = _cache[ticker]
        return data
    
    try:
        logger.info(f"Fetching fresh data for {ticker}")
        stock = yf.Ticker(ticker)
        
        # 直近のデータを取得（5日分）
        hist = stock.history(period="5d")
        
        if hist.empty:
            logger.warning(f"No historical data found for {ticker}")
            error_data = create_error_data(
                ticker, 
                "データが取得できませんでした", 
                timestamp_str
            )
            # エラーデータもキャッシュ（短いTTL）
            with _cache_lock:
                _cache[ticker] = (error_data, now)
            return error_data
        
        # 価格計算
        current_price = hist['Close'].iloc[-1]
        prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
        
        # NaNチェック（価格データの妥当性確認）
        if math.isnan(current_price) or math.isnan(prev_price):
            logger.error(f"Invalid price data (NaN) for {ticker}")
            error_data = create_error_data(
                ticker, 
                "価格データに不正な値が含まれています", 
                timestamp_str
            )
            with _cache_lock:
                _cache[ticker] = (error_data, now)
            return error_data
        
        change = current_price - prev_price
        change_percent = (change / prev_price) * 100 if prev_price != 0 else 0
        
        # チャートデータ（直近5日）
        chart_data = []
        for date, row in hist.iterrows():
            close_value = row['Close']
            # NaN値をスキップして、有効なデータのみ追加
            if not math.isnan(close_value):
                chart_data.append({
                    "date": date.strftime("%m/%d"),
                    "close": round(close_value, 2)
                })
        
        # 出来高の処理（NaN対策）
        volume_value = hist['Volume'].iloc[-1]
        volume = int(volume_value) if not math.isnan(volume_value) else 0
        
        data = {
            "ticker": ticker,
            "name": STOCKS.get(ticker, ticker),
            "current_price": round(current_price, 2),
            "change": round(change, 2),
            "change_percent": round(change_percent, 2),
            "volume": volume,
            "chart_data": chart_data,
            "last_update": timestamp_str,
            "error": False
        }
        
        # キャッシュに保存（スレッドセーフ）
        with _cache_lock:
            _cache[ticker] = (data, now)
        
        return data
        
    except Exception as e:
        logger.error(f"Error fetching data for {ticker}: {e}", exc_info=True)
        error_data = create_error_data(
            ticker, 
            "データの取得に失敗しました", 
            timestamp_str
        )
        # エラーデータもキャッシュ（短いTTL）
        with _cache_lock:
            _cache[ticker] = (error_data, now)
        return error_data


def get_all_stocks_data() -> List[Dict]:
    """
    全銘柄の株価データを取得
    
    Returns:
        株価データのリスト（常に全銘柄分のデータを返す）
    """
    stocks_data = []
    for ticker in STOCKS.keys():
        data = get_stock_data(ticker)
        stocks_data.append(data)
    return stocks_data


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """メインページ"""
    stocks_data = get_all_stocks_data()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "stocks": stocks_data}
    )


@app.get("/api/stocks")
async def get_stocks():
    """株価データAPI（JSON形式）"""
    stocks_data = get_all_stocks_data()
    return {"stocks": stocks_data, "timestamp": get_jst_now().isoformat()}


@app.get("/api/stocks/partial", response_class=HTMLResponse)
async def get_stocks_partial(request: Request):
    """部分更新用のHTMLを返す（HTMX用）"""
    stocks_data = get_all_stocks_data()
    return templates.TemplateResponse(
        "stocks_partial.html",
        {"request": request, "stocks": stocks_data}
    )


@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    with _cache_lock:
        cache_size = len(_cache)
    return {
        "status": "healthy",
        "timestamp": get_jst_now().isoformat(),
        "cache_size": cache_size
    }


@app.get("/api/cache/clear")
async def clear_cache():
    """キャッシュをクリア（デバッグ用）"""
    with _cache_lock:
        cache_count = len(_cache)
        _cache.clear()
    logger.info(f"Cache cleared: {cache_count} entries removed")
    return {"message": f"Cache cleared: {cache_count} entries removed"}


if __name__ == "__main__":
    # Railway環境ではPORT環境変数を使用
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
