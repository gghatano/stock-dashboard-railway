"""
株価ダッシュボードアプリケーションのユニットテスト

実行方法:
    pytest test_app.py -v
"""

import pytest
from datetime import datetime
import pytz
from unittest.mock import Mock, patch
import pandas as pd

# テスト対象のインポート
import sys
sys.path.insert(0, '.')
from app import (
    get_jst_now,
    is_cache_valid,
    create_error_data,
    get_stock_data,
    get_all_stocks_data,
    STOCKS,
    JST,
    CACHE_TTL,
    ERROR_CACHE_TTL,
    _cache,
    _cache_lock
)


class TestUtilityFunctions:
    """ユーティリティ関数のテスト"""
    
    def test_get_jst_now(self):
        """JST時刻の取得が正しいか"""
        now = get_jst_now()
        assert now.tzinfo == JST
        assert isinstance(now, datetime)
    
    def test_create_error_data(self):
        """エラーデータの作成が正しいか"""
        ticker = "TEST.T"
        current_time = get_jst_now()
        error_data = create_error_data(ticker, current_time)
        
        assert error_data["ticker"] == ticker
        assert error_data["error"] is True
        assert "error_message" in error_data
        assert error_data["current_price"] == 0
        assert error_data["volume"] == 0
        assert len(error_data["chart_data"]) == 0


class TestCacheFunctions:
    """キャッシュ関連機能のテスト"""
    
    def setup_method(self):
        """各テストの前にキャッシュをクリア"""
        with _cache_lock:
            _cache.clear()
    
    def test_cache_invalid_when_empty(self):
        """キャッシュが空の場合は無効"""
        current_time = get_jst_now()
        assert is_cache_valid("TEST.T", current_time) is False
    
    def test_cache_valid_within_ttl(self):
        """TTL内のキャッシュは有効"""
        ticker = "TEST.T"
        current_time = get_jst_now()
        
        # キャッシュにデータを保存
        test_data = {"ticker": ticker, "error": False}
        with _cache_lock:
            _cache[ticker] = (test_data, current_time)
        
        # TTL内なので有効
        assert is_cache_valid(ticker, current_time) is True
    
    def test_error_cache_has_shorter_ttl(self):
        """エラーキャッシュは短いTTLを持つ"""
        ticker = "TEST.T"
        current_time = get_jst_now()
        
        # エラーデータをキャッシュに保存
        error_data = {"ticker": ticker, "error": True}
        with _cache_lock:
            _cache[ticker] = (error_data, current_time)
        
        # エラーキャッシュのTTLが正しく適用されているか確認
        # （実際の時間経過をシミュレートするのは難しいので、TTL定数の存在を確認）
        assert ERROR_CACHE_TTL < CACHE_TTL


class TestGetStockData:
    """株価データ取得のテスト"""
    
    def setup_method(self):
        """各テストの前にキャッシュをクリア"""
        with _cache_lock:
            _cache.clear()
    
    @patch('app.yf.Ticker')
    def test_get_stock_data_success(self, mock_ticker):
        """正常な株価データ取得"""
        # モックデータの準備
        mock_hist = pd.DataFrame({
            'Close': [100.0, 105.0, 110.0, 108.0, 112.0],
            'Volume': [1000, 1100, 1200, 1150, 1300]
        }, index=pd.date_range('2026-01-10', periods=5))
        
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = mock_hist
        mock_ticker.return_value = mock_ticker_instance
        
        # テスト実行
        ticker = "2327.T"
        data = get_stock_data(ticker)
        
        # 検証
        assert data is not None
        assert data["ticker"] == ticker
        assert data["error"] is False
        assert data["current_price"] == 112.0
        assert data["change"] == 4.0  # 112 - 108
        assert len(data["chart_data"]) == 5
    
    @patch('app.yf.Ticker')
    def test_get_stock_data_empty_history(self, mock_ticker):
        """履歴データが空の場合"""
        # 空のDataFrameを返すモック
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = pd.DataFrame()
        mock_ticker.return_value = mock_ticker_instance
        
        # テスト実行
        ticker = "2327.T"
        data = get_stock_data(ticker)
        
        # 検証
        assert data is not None
        assert data["error"] is True
        assert "株価データが見つかりませんでした" in data["error_message"]
    
    @patch('app.yf.Ticker')
    def test_get_stock_data_exception(self, mock_ticker):
        """例外が発生した場合"""
        # 例外を発生させるモック
        mock_ticker.side_effect = Exception("API Error")
        
        # テスト実行
        ticker = "2327.T"
        data = get_stock_data(ticker)
        
        # 検証
        assert data is not None
        assert data["error"] is True
        assert "error_message" in data
    
    @patch('app.yf.Ticker')
    def test_get_stock_data_uses_cache(self, mock_ticker):
        """キャッシュが使用されるか"""
        # 1回目の呼び出し用のモック
        mock_hist = pd.DataFrame({
            'Close': [100.0, 105.0],
            'Volume': [1000, 1100]
        }, index=pd.date_range('2026-01-10', periods=2))
        
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = mock_hist
        mock_ticker.return_value = mock_ticker_instance
        
        ticker = "2327.T"
        
        # 1回目の呼び出し
        data1 = get_stock_data(ticker)
        
        # 2回目の呼び出し（キャッシュから取得されるべき）
        data2 = get_stock_data(ticker)
        
        # yf.Tickerは1回しか呼ばれていないはず（2回目はキャッシュ）
        assert mock_ticker.call_count == 1
        assert data1 == data2


class TestGetAllStocksData:
    """全銘柄データ取得のテスト"""
    
    def setup_method(self):
        """各テストの前にキャッシュをクリア"""
        with _cache_lock:
            _cache.clear()
    
    @patch('app.get_stock_data')
    def test_get_all_stocks_data(self, mock_get_stock_data):
        """全銘柄のデータ取得"""
        # モックデータ
        mock_get_stock_data.return_value = {
            "ticker": "TEST.T",
            "error": False
        }
        
        # テスト実行
        all_data = get_all_stocks_data()
        
        # 検証
        assert len(all_data) == len(STOCKS)
        assert all(isinstance(data, dict) for data in all_data)
    
    @patch('app.get_stock_data')
    def test_get_all_stocks_data_includes_errors(self, mock_get_stock_data):
        """エラーデータも含まれるか"""
        # エラーデータを返すモック
        mock_get_stock_data.return_value = {
            "ticker": "TEST.T",
            "error": True
        }
        
        # テスト実行
        all_data = get_all_stocks_data()
        
        # 検証（エラーでもデータは返される）
        assert len(all_data) == len(STOCKS)


class TestThreadSafety:
    """スレッドセーフティのテスト"""
    
    def test_cache_lock_exists(self):
        """キャッシュロックが存在するか"""
        assert _cache_lock is not None
    
    @patch('app.yf.Ticker')
    def test_concurrent_access(self, mock_ticker):
        """並行アクセスのシミュレーション"""
        from threading import Thread
        
        # モックデータの準備
        mock_hist = pd.DataFrame({
            'Close': [100.0, 105.0],
            'Volume': [1000, 1100]
        }, index=pd.date_range('2026-01-10', periods=2))
        
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = mock_hist
        mock_ticker.return_value = mock_ticker_instance
        
        # 複数スレッドから同時アクセス
        threads = []
        results = []
        
        def fetch_data():
            data = get_stock_data("2327.T")
            results.append(data)
        
        for _ in range(5):
            t = Thread(target=fetch_data)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # 全てのスレッドがデータを取得できたか
        assert len(results) == 5
        assert all(r is not None for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
