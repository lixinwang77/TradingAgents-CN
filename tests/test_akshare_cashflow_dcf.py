"""
测试 AkShare 财务数据在现金流量表和 DCF 估值工具中的正确读取。

验证：
1. get_cash_flow_statement 能读取到经营活动现金流量净额
2. DCF 估值能识别至少一个年报期（1231）
3. 不虚构缺失的投资/筹资现金流数据
"""

import pytest
from datetime import datetime, timezone
from typing import Dict, Any
import json


@pytest.fixture
def akshare_financial_document_with_cashflow() -> Dict[str, Any]:
    """模拟含现金流的 AkShare 格式财务文档"""
    return {
        "symbol": "601985",
        "code": "601985",
        "name": "中国核电",
        "data_source": "akshare",
        "report_period": "20251231",
        "report_type": "annual",
        "updated_at": datetime.now(timezone.utc),
        "raw_data": {
            "main_indicators": [
                {
                    "指标": "营业收入",
                    "20251231": "82075000000",
                    "20250930": "60000000000",
                    "20250630": "38398000000",
                    "20241231": "75000000000",
                },
                {
                    "指标": "净利润",
                    "20251231": "9304000000",
                    "20250930": "7000000000",
                    "20250630": "3641000000",
                    "20241231": "8500000000",
                },
                {
                    "指标": "总资产",
                    "20251231": "500000000000",
                    "20250930": "480000000000",
                    "20250630": "470000000000",
                    "20241231": "460000000000",
                },
                {
                    "指标": "负债合计",
                    "20251231": "300000000000",
                    "20250930": "290000000000",
                    "20250630": "285000000000",
                    "20241231": "280000000000",
                },
                {
                    "指标": "股东权益合计",
                    "20251231": "200000000000",
                    "20250930": "190000000000",
                    "20250630": "185000000000",
                    "20241231": "180000000000",
                },
                {
                    "指标": "净资产收益率(ROE)",
                    "20251231": "8.21",
                    "20250930": "5.8",
                    "20250630": "3.05",
                    "20241231": "7.5",
                },
                {
                    "指标": "资产负债率",
                    "20251231": "60.0",
                    "20250930": "60.4",
                    "20250630": "70.45",
                    "20241231": "60.9",
                },
                {
                    "指标": "经营活动产生的现金流量净额",
                    "20251231": "25000000000",
                    "20250930": "18000000000",
                    "20250630": "12000000000",
                    "20241231": "22000000000",
                },
            ]
        }
    }


@pytest.fixture
def akshare_financial_document_with_short_cashflow_label() -> Dict[str, Any]:
    """模拟实际 AkShare 数据使用短标签（经营现金流量净额）而非长标签"""
    return {
        "symbol": "601985",
        "code": "601985",
        "name": "中国核电",
        "data_source": "akshare",
        "report_period": "20251231",
        "updated_at": datetime.now(timezone.utc),
        "raw_data": {
            "main_indicators": [
                {
                    "指标": "营业收入",
                    "20251231": "82075000000",
                    "20250930": "60000000000",
                    "20250630": "38398000000",
                    "20241231": "75000000000",
                },
                {
                    "指标": "净利润",
                    "20251231": "9304000000",
                    "20250930": "7000000000",
                    "20250630": "3641000000",
                    "20241231": "8500000000",
                },
                {
                    "指标": "总资产",
                    "20251231": "500000000000",
                    "20250930": "480000000000",
                    "20250630": "470000000000",
                    "20241231": "460000000000",
                },
                {
                    "指标": "负债合计",
                    "20251231": "300000000000",
                    "20250930": "290000000000",
                    "20250630": "285000000000",
                    "20241231": "280000000000",
                },
                {
                    "指标": "股东权益合计",
                    "20251231": "200000000000",
                    "20250930": "190000000000",
                    "20250630": "185000000000",
                    "20241231": "180000000000",
                },
                {
                    "指标": "净资产收益率(ROE)",
                    "20251231": "8.21",
                    "20250930": "5.8",
                    "20250630": "3.05",
                    "20241231": "7.5",
                },
                {
                    "指标": "资产负债率",
                    "20251231": "60.0",
                    "20250930": "60.4",
                    "20250630": "70.45",
                    "20241231": "60.9",
                },
                {
                    "指标": "经营现金流量净额",  # 短标签，实际 AkShare 使用
                    "20251231": "25000000000",
                    "20250930": "18000000000",
                    "20250630": "12000000000",
                    "20241231": "22000000000",
                },
            ]
        }
    }


@pytest.fixture
def mock_mongodb_collection(akshare_financial_document_with_cashflow):
    """模拟 MongoDB 集合"""
    class MockCursor:
        def __init__(self, data):
            self.data = [data] if data else []
        
        def sort(self, *args, **kwargs):
            return self
        
        def limit(self, n):
            return self
        
        def __iter__(self):
            return iter(self.data)
        
        def to_list(self, length=None):
            return self.data
    
    class MockCollection:
        def find_one(self, query, **kwargs):
            return akshare_financial_document_with_cashflow
        
        def find(self, query, *args, **kwargs):
            return MockCursor(akshare_financial_document_with_cashflow)
    
    return MockCollection()


@pytest.fixture
def mock_mongodb_client(mock_mongodb_collection):
    """模拟 MongoDB 客户端"""
    class MockDB:
        def __init__(self):
            self.stock_financial_data = mock_mongodb_collection
            self.financial_data_cache = mock_mongodb_collection
            self.stock_financial_periods = mock_mongodb_collection
            self.stock_basic_info = mock_mongodb_collection
            self.market_quotes = mock_mongodb_collection
        
        def __getitem__(self, key):
            # Support db['collection_name'] syntax
            return getattr(self, key, mock_mongodb_collection)
    
    class MockClient:
        def get_database(self, name):
            return MockDB()
    
    return MockClient()


def test_cash_flow_statement_reads_akshare_data(monkeypatch, mock_mongodb_client, akshare_financial_document_with_cashflow):
    """测试 get_cash_flow_statement 能读取 AkShare 现金流数据"""
    # Mock get_mongodb_client at all levels
    def mock_get_client():
        return mock_mongodb_client
    
    monkeypatch.setattr(
        'tradingagents.dataflows.cache.app_adapter.get_mongodb_client',
        mock_get_client
    )
    
    # Mock _get_db to return the mock database
    def mock_get_db():
        return mock_mongodb_client.get_database('tradingagents')
    
    monkeypatch.setattr(
        'core.skill_runtime.data_access._get_db',
        mock_get_db
    )
    
    from core.tools.implementations.fundamentals.stock_fundamentals import get_cash_flow_statement
    
    result = get_cash_flow_statement.invoke({"ticker": "601985", "limit": 4})
    
    # 不应返回"暂未获取到"错误
    assert "暂未获取到最近季度现金流量表数据" not in result, f"现金流量表应有数据，但得到：{result[:200]}"
    
    # 应包含标题
    assert "601985" in result
    assert "现金流量表" in result
    
    # 应包含经营活动现金流量净额数据
    assert "经营活动现金流量净额" in result or "n_cashflow_act" in result
    
    # 应包含至少一个报告期
    assert "2025" in result or "20251231" in result or "2025-12-31" in result


def test_dcf_recognizes_annual_periods(monkeypatch, mock_mongodb_client, akshare_financial_document_with_cashflow):
    """测试 DCF 估值能识别年报期"""
    # Mock get_mongodb_client at all levels
    def mock_get_client():
        return mock_mongodb_client
    
    monkeypatch.setattr(
        'tradingagents.dataflows.cache.app_adapter.get_mongodb_client',
        mock_get_client
    )
    
    # Mock _get_db to return the mock database
    def mock_get_db():
        return mock_mongodb_client.get_database('tradingagents')
    
    monkeypatch.setattr(
        'core.skill_runtime.data_access._get_db',
        mock_get_db
    )
    
    # Mock get_latest_stock_price to return a valid price
    def mock_get_price(symbol):
        return 5.50
    
    monkeypatch.setattr(
        'core.skill_runtime.data_access.get_latest_stock_price',
        mock_get_price
    )
    
    # Mock get_stock_basic_info to return basic info with shares
    def mock_get_basic_info(symbol):
        return {
            "symbol": symbol,
            "name": "中国核电",
            "total_share": 1256000,  # 万股
        }
    
    monkeypatch.setattr(
        'core.skill_runtime.data_access.get_stock_basic_info',
        mock_get_basic_info
    )
    
    from core.tools.implementations.fundamentals.valuation.dcf_valuation import get_dcf_valuation
    
    result_str = get_dcf_valuation.invoke({"symbol": "601985"})
    result = json.loads(result_str)
    
    # 不应返回"可用年报数据不足"错误
    assert result.get("status") != "error", f"DCF 应成功，但得到错误：{result.get('message')}"
    
    # 应至少有 2 个年报期
    data_quality = result.get("data_quality", {})
    years_available = data_quality.get("years_available", 0)
    assert years_available >= 2, f"应至少有 2 个年报期，实际 {years_available}"
    
    # 应有估值结果
    assert "valuation" in result
    valuation = result["valuation"]
    assert valuation.get("per_share_value") is not None
    assert valuation.get("enterprise_value") is not None


def test_cash_flow_does_not_invent_missing_data(monkeypatch, mock_mongodb_client):
    """测试现金流量表不虚构缺失的投资/筹资现金流"""
    # Mock get_mongodb_client
    def mock_get_client():
        return mock_mongodb_client
    
    monkeypatch.setattr(
        'tradingagents.dataflows.cache.app_adapter.get_mongodb_client',
        mock_get_client
    )
    
    from tradingagents.dataflows.optimized_china_data import OptimizedChinaDataProvider
    from core.skill_runtime.data_access import expand_financial_document_to_periods
    
    provider = OptimizedChinaDataProvider()
    
    # 获取缓存数据
    cached_data = provider._get_cached_raw_financial_data("601985")
    
    assert cached_data is not None, "应能获取缓存数据"
    assert 'cash_flow' in cached_data, "应包含 cash_flow 字段"
    
    # 现金流记录应该存在
    cash_flow_records = cached_data['cash_flow']
    assert len(cash_flow_records) > 0, "应有现金流记录"
    
    # 检查记录中是否有经营现金流
    for record in cash_flow_records:
        # 应有经营现金流
        assert record.get('n_cashflow_act') is not None, f"记录应包含经营现金流: {record}"
        
        # 不应虚构投资/筹资现金流（原始数据中没有）
        # 如果存在 n_cashflow_inv_act 或 n_cashflow_fin_act，应该是 None 或不存在
        inv_cf = record.get('n_cashflow_inv_act')
        fin_cf = record.get('n_cashflow_fin_act')
        
        # 原始数据中没有投资/筹资现金流，所以这些字段应该不存在或为 None
        assert inv_cf is None, f"不应虚构投资现金流，但得到: {inv_cf}"
        assert fin_cf is None, f"不应虚构筹资现金流，但得到: {fin_cf}"


def test_annual_period_report_type_preserved(monkeypatch, mock_mongodb_client):
    """测试年报 report_type 字段正确保留"""
    # Mock get_mongodb_client
    def mock_get_client():
        return mock_mongodb_client
    
    monkeypatch.setattr(
        'tradingagents.dataflows.cache.app_adapter.get_mongodb_client',
        mock_get_client
    )
    
    from tradingagents.dataflows.optimized_china_data import OptimizedChinaDataProvider
    from core.skill_runtime.data_access import expand_financial_document_to_periods
    
    provider = OptimizedChinaDataProvider()
    
    # 获取并展开数据
    raw_doc = mock_mongodb_client.get_database('tradingagents').stock_financial_data.find_one({})
    pivoted_doc = provider._pivot_akshare_wide_table(raw_doc)
    expanded_periods = expand_financial_document_to_periods(pivoted_doc)
    
    # 找到 20251231 年报期
    annual_period = next((p for p in expanded_periods if p.get('report_period') == '20251231'), None)
    assert annual_period is not None, "应找到 20251231 年报期"
    
    # 验证 report_type 字段
    assert annual_period.get('report_type') == 'annual', f"20251231 应标记为 annual，实际: {annual_period.get('report_type')}"
    
    # 聚合后的数据也应保留 report_type
    aggregated_data = provider._aggregate_periods_to_financial_data(expanded_periods)
    
    # 检查利润表记录
    income_records = aggregated_data['income_statement']
    annual_income = next((r for r in income_records if str(r.get('report_period')).endswith('1231')), None)
    assert annual_income is not None, "聚合后应有 1231 利润表记录"
    assert annual_income.get('report_type') == 'annual', f"聚合后的 1231 记录应标记为 annual，实际: {annual_income.get('report_type')}"


def test_financial_periods_api_returns_annual_records(monkeypatch, mock_mongodb_client, akshare_financial_document_with_cashflow):
    """测试 get_stock_financial_periods 返回年报记录"""
    # Mock get_mongodb_client at all levels
    def mock_get_client():
        return mock_mongodb_client
    
    monkeypatch.setattr(
        'tradingagents.dataflows.cache.app_adapter.get_mongodb_client',
        mock_get_client
    )
    
    # Mock _get_db to return the mock database
    def mock_get_db():
        return mock_mongodb_client.get_database('tradingagents')
    
    monkeypatch.setattr(
        'core.skill_runtime.data_access._get_db',
        mock_get_db
    )
    
    from core.skill_runtime.data_access import get_stock_financial_periods
    
    periods = get_stock_financial_periods("601985", limit=20)
    
    # 应返回多个期间
    assert len(periods) > 0, "应返回至少一个期间"
    
    # 找到年报期
    annual_periods = [p for p in periods if str(p.get('report_period', '')).endswith('1231')]
    assert len(annual_periods) >= 2, f"应至少有 2 个年报期，实际 {len(annual_periods)}"
    
    # 验证年报期有 report_type 标记
    for ap in annual_periods:
        assert ap.get('report_type') == 'annual', f"年报期应标记为 annual: {ap.get('report_period')}"


def test_short_cashflow_label_in_analyst_tool(monkeypatch, akshare_financial_document_with_short_cashflow_label):
    """测试 get_cash_flow_statement 识别短标签经营现金流量净额"""
    class MockCursor:
        def __init__(self, data):
            self.data = [data] if data else []
        
        def sort(self, *args, **kwargs):
            return self
        
        def limit(self, n):
            return self
        
        def __iter__(self):
            return iter(self.data)
        
        def to_list(self, length=None):
            return self.data
    
    class MockCollection:
        def find_one(self, query, **kwargs):
            return akshare_financial_document_with_short_cashflow_label
        
        def find(self, query, *args, **kwargs):
            return MockCursor(akshare_financial_document_with_short_cashflow_label)
    
    class MockDB:
        def __init__(self):
            self.stock_financial_data = MockCollection()
            self.financial_data_cache = MockCollection()
            self.stock_financial_periods = MockCollection()
            self.stock_basic_info = MockCollection()
            self.market_quotes = MockCollection()
        
        def __getitem__(self, key):
            return getattr(self, key, MockCollection())
    
    class MockClient:
        def get_database(self, name):
            return MockDB()
    
    mock_client = MockClient()
    
    def mock_get_client():
        return mock_client
    
    def mock_get_db():
        return mock_client.get_database('tradingagents')
    
    monkeypatch.setattr(
        'tradingagents.dataflows.cache.app_adapter.get_mongodb_client',
        mock_get_client
    )
    monkeypatch.setattr(
        'core.skill_runtime.data_access._get_db',
        mock_get_db
    )
    
    from core.tools.implementations.fundamentals.stock_fundamentals import get_cash_flow_statement
    
    result = get_cash_flow_statement.invoke({"ticker": "601985", "limit": 4})
    
    # 不应返回"暂未获取到"错误
    assert "暂未获取到最近季度现金流量表数据" not in result, f"现金流量表应有数据（短标签），但得到：{result[:200]}"
    
    # 应包含经营活动现金流量净额数据
    assert "经营活动现金流量净额" in result or "n_cashflow_act" in result, f"应包含现金流数据，结果：{result[:500]}"
    
    # 应包含至少一个报告期
    assert "2025" in result or "20251231" in result or "2025-12-31" in result


def _live_akshare_wide_table_only_doc() -> Dict[str, Any]:
    """Live Mongo shape: raw_data has only main_indicators, label 经营现金流量净额.

    No cashflow_statement key, no report_type, no investing/financing rows.
    """
    return {
        "symbol": "601985",
        "code": "601985",
        "name": "中国核电",
        "data_source": "akshare",
        "report_period": "20260630",
        "updated_at": datetime.now(timezone.utc),
        "raw_data": {
            "main_indicators": [
                {
                    "指标": "营业总收入",
                    "20251231": "82075000000",
                    "20250930": "61635000000",
                    "20250630": "38398000000",
                    "20241231": "75000000000",
                    "20231231": "68000000000",
                },
                {
                    "指标": "归母净利润",
                    "20251231": "9304000000",
                    "20250930": "8002000000",
                    "20250630": "3641000000",
                    "20241231": "8500000000",
                    "20231231": "7800000000",
                },
                {
                    "指标": "经营现金流量净额",
                    "20251231": "25000000000",
                    "20250930": "18000000000",
                    "20250630": "12000000000",
                    "20241231": "22000000000",
                    "20231231": "20000000000",
                },
            ]
        },
    }


def _live_quarterly_period_stub() -> Dict[str, Any]:
    """Live stock_financial_periods shape: one quarterly row, no wide table."""
    return {
        "symbol": "601985",
        "code": "601985",
        "name": "中国核电",
        "source": "akshare",
        "data_source": "akshare",
        "report_period": "20260630",
        "report_date": "20260630",
        "report_type": "quarterly",
    }


class _DocsCursor:
    def __init__(self, docs):
        self.data = list(docs or [])

    def sort(self, *args, **kwargs):
        return self

    def limit(self, n):
        self.data = self.data[:n]
        return self

    def __iter__(self):
        return iter(self.data)


class _DocsCollection:
    def __init__(self, docs):
        self.docs = list(docs or [])

    def find_one(self, query=None, **kwargs):
        return self.docs[0] if self.docs else None

    def find(self, query=None, *args, **kwargs):
        return _DocsCursor(self.docs)


class _SplitMockDB:
    def __init__(self, snapshot_docs, period_docs):
        self.stock_financial_data = _DocsCollection(snapshot_docs)
        self.financial_data_cache = _DocsCollection(snapshot_docs)
        self.stock_financial_periods = _DocsCollection(period_docs)
        self.stock_basic_info = _DocsCollection([])
        self.market_quotes = _DocsCollection([])

    def __getitem__(self, key):
        return getattr(self, key, _DocsCollection([]))


class _SplitMockClient:
    def __init__(self, snapshot_docs, period_docs):
        self._db = _SplitMockDB(snapshot_docs, period_docs)

    def get_database(self, name):
        return self._db


def _patch_financial_db(monkeypatch, snapshot_docs, period_docs):
    client = _SplitMockClient(snapshot_docs, period_docs)

    monkeypatch.setattr(
        "tradingagents.dataflows.cache.app_adapter.get_mongodb_client",
        lambda: client,
    )
    monkeypatch.setattr(
        "core.skill_runtime.data_access._get_db",
        lambda: client.get_database("tradingagents"),
    )
    monkeypatch.setattr(
        "core.skill_runtime.data_access._get_sources",
        lambda market="a_shares": ["akshare"],
    )
    monkeypatch.setattr(
        "core.skill_runtime.data_access.get_latest_stock_price",
        lambda symbol: 5.50,
    )
    monkeypatch.setattr(
        "core.skill_runtime.data_access.get_stock_basic_info",
        lambda symbol: {"symbol": symbol, "name": "中国核电", "total_share": 1256000},
    )
    return client


def test_expand_wide_table_only_maps_short_cashflow_label():
    """Wide table with 经营现金流量净额 and no cashflow_statement still expands."""
    from core.skill_runtime.data_access import expand_financial_document_to_periods

    doc = _live_akshare_wide_table_only_doc()
    assert "cashflow_statement" not in doc["raw_data"]
    assert "report_type" not in doc

    periods = expand_financial_document_to_periods(doc)
    annual = [p for p in periods if str(p.get("report_period", "")).endswith("1231")]
    assert len(annual) >= 1, f"宽表应展开出 1231 年报期，实际 {[p.get('report_period') for p in periods]}"

    latest_annual = next(p for p in annual if p.get("report_period") == "20251231")
    assert latest_annual.get("report_type") == "annual"
    assert latest_annual.get("n_cashflow_act") == 25000000000.0
    assert latest_annual.get("n_cashflow_inv_act") is None
    assert latest_annual.get("n_cashflow_fin_act") is None


def test_periods_api_ignores_quarterly_stub_and_expands_wide_table(monkeypatch):
    """Live DCF failure: periods collection has 20260630 quarterly, snapshot is wide table."""
    _patch_financial_db(
        monkeypatch,
        snapshot_docs=[_live_akshare_wide_table_only_doc()],
        period_docs=[_live_quarterly_period_stub()],
    )
    from core.skill_runtime.data_access import get_stock_financial_periods

    periods = get_stock_financial_periods("601985", limit=20)
    annual = [p for p in periods if str(p.get("report_period", "")).endswith("1231")]
    assert len(annual) >= 1, (
        f"DCF 读路径应看到 1231 年报期，不能停在 20260630 季报。实际: "
        f"{[(p.get('report_period'), p.get('report_type')) for p in periods]}"
    )
    assert all(p.get("report_type") == "annual" for p in annual)


def test_cash_flow_and_dcf_from_wide_table_only_live_shape(monkeypatch):
    """Analyst cash-flow tool and DCF against the live Mongo shape."""
    _patch_financial_db(
        monkeypatch,
        snapshot_docs=[_live_akshare_wide_table_only_doc()],
        period_docs=[_live_quarterly_period_stub()],
    )

    from core.tools.implementations.fundamentals.stock_fundamentals import get_cash_flow_statement
    from core.tools.implementations.fundamentals.valuation.dcf_valuation import get_dcf_valuation

    cash_result = get_cash_flow_statement.invoke({"ticker": "601985", "limit": 4})
    assert cash_result != "601985 暂未获取到最近季度现金流量表数据。"
    assert "暂未获取到最近季度现金流量表数据" not in cash_result
    assert "经营活动现金流量净额" in cash_result
    assert "25000000000" in cash_result or "250.00亿" in cash_result or "250.0亿" in cash_result

    raw_investing = [line for line in cash_result.splitlines() if "投资活动现金流量净额（原始累计）" in line]
    raw_financing = [line for line in cash_result.splitlines() if "筹资活动现金流量净额（原始累计）" in line]
    for line in raw_investing + raw_financing:
        assert "N/A" in line or not any(ch.isdigit() for ch in line), (
            f"缺少投资/筹资行时不应编造数字: {line}"
        )

    dcf_result = json.loads(get_dcf_valuation.invoke({"symbol": "601985"}))
    assert dcf_result.get("message") != "可用年报数据不足（仅 0 期），无法进行 DCF 估值"
    assert dcf_result.get("status") != "error" or "仅 0 期" not in str(dcf_result.get("message")), (
        f"DCF 应看到至少 1 个年报期，实际: {dcf_result}"
    )
    if dcf_result.get("status") != "error":
        years_available = (dcf_result.get("data_quality") or {}).get("years_available", 0)
        assert years_available >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

