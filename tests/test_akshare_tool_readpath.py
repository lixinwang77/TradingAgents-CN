"""
测试 AkShare 财务数据在工具读取路径中的正确展开和读取。

本测试验证：
1. OptimizedChinaDataProvider._get_cached_raw_financial_data 能识别 AkShare 宽表格式
2. 使用 expand_financial_document_to_periods 正确展开
3. 工具能获取到营收、净利润、ROE、资产负债率、经营现金流等关键指标
4. 至少返回一个 1231 年报期
"""

import pytest
from datetime import datetime, timezone
from typing import Dict, Any


@pytest.fixture
def akshare_financial_document() -> Dict[str, Any]:
    """模拟 AkShare 格式的财务文档（宽表格式，含 main_indicators）"""
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
                    "20251231": "120000000000",
                    "20250930": "90000000000",
                    "20250630": "60000000000",
                },
                {
                    "指标": "净利润",
                    "20251231": "15000000000",
                    "20250930": "11000000000",
                    "20250630": "7500000000",
                },
                {
                    "指标": "总资产",
                    "20251231": "500000000000",
                    "20250930": "480000000000",
                    "20250630": "470000000000",
                },
                {
                    "指标": "负债合计",
                    "20251231": "300000000000",
                    "20250930": "290000000000",
                    "20250630": "285000000000",
                },
                {
                    "指标": "股东权益合计",
                    "20251231": "200000000000",
                    "20250930": "190000000000",
                    "20250630": "185000000000",
                },
                {
                    "指标": "净资产收益率(ROE)",
                    "20251231": "7.5",
                    "20250930": "5.8",
                    "20250630": "4.1",
                },
                {
                    "指标": "资产负债率",
                    "20251231": "60.0",
                    "20250930": "60.4",
                    "20250630": "60.6",
                },
                {
                    "指标": "经营活动产生的现金流量净额",
                    "20251231": "25000000000",
                    "20250930": "18000000000",
                    "20250630": "12000000000",
                },
            ]
        }
    }


@pytest.fixture
def mock_mongodb_collection(akshare_financial_document):
    """模拟 MongoDB 集合"""
    class MockCollection:
        def find_one(self, query, **kwargs):
            return akshare_financial_document
    
    return MockCollection()


@pytest.fixture
def mock_mongodb_client(mock_mongodb_collection):
    """模拟 MongoDB 客户端"""
    class MockDB:
        stock_financial_data = mock_mongodb_collection
        financial_data_cache = mock_mongodb_collection
    
    class MockClient:
        def get_database(self, name):
            return MockDB()
    
    return MockClient()


def test_pivot_and_expand_akshare_document(akshare_financial_document):
    """测试 pivot + expand 流程正确处理 AkShare 宽表"""
    from tradingagents.dataflows.optimized_china_data import OptimizedChinaDataProvider
    from core.skill_runtime.data_access import expand_financial_document_to_periods
    
    provider = OptimizedChinaDataProvider()
    
    # 第一步：pivot 宽表为按期格式
    pivoted_doc = provider._pivot_akshare_wide_table(akshare_financial_document)
    
    # 验证 pivot 结果
    assert 'raw_data' in pivoted_doc
    raw_data = pivoted_doc['raw_data']
    assert 'income_statement' in raw_data
    assert 'balance_sheet' in raw_data
    assert 'cashflow_statement' in raw_data
    assert 'financial_indicators' in raw_data
    
    # 第二步：expand 展开为多期记录
    periods = expand_financial_document_to_periods(pivoted_doc)
    
    # 应该至少有 3 个报告期
    assert len(periods) >= 3, f"期望至少 3 个报告期，实际 {len(periods)}"
    
    # 找到 20251231 年报期
    annual_period = next((p for p in periods if p.get('report_period') == '20251231'), None)
    assert annual_period is not None, "未找到 20251231 年报期"
    assert annual_period.get('report_type') == 'annual', f"20251231 应为年报，实际 {annual_period.get('report_type')}"
    
    # 验证关键指标是否提取正确
    assert annual_period.get('revenue') is not None, "营业收入缺失"
    assert annual_period.get('net_income') is not None, "净利润缺失"
    assert annual_period.get('total_assets') is not None, "总资产缺失"
    assert annual_period.get('total_liab') is not None, "负债合计缺失"
    assert annual_period.get('total_equity') is not None, "股东权益缺失"
    assert annual_period.get('roe') is not None, "ROE 缺失"
    assert annual_period.get('debt_to_assets') is not None, "资产负债率缺失"
    assert annual_period.get('n_cashflow_act') is not None, "经营现金流缺失"
    
    # 验证数值范围合理
    assert annual_period['revenue'] == 120000000000.0, f"营业收入应为 120000000000，实际 {annual_period['revenue']}"
    assert annual_period['net_income'] == 15000000000.0, f"净利润应为 15000000000，实际 {annual_period['net_income']}"
    assert annual_period['roe'] == 7.5, f"ROE 应为 7.5，实际 {annual_period['roe']}"
    assert annual_period['debt_to_assets'] == 60.0, f"资产负债率应为 60.0，实际 {annual_period['debt_to_assets']}"
    assert annual_period['n_cashflow_act'] == 25000000000.0, f"经营现金流应为 25000000000，实际 {annual_period['n_cashflow_act']}"


def test_cache_loader_recognizes_akshare_format(monkeypatch, mock_mongodb_client, akshare_financial_document):
    """测试缓存加载器能识别并展开 AkShare 格式"""
    # Mock get_mongodb_client
    def mock_get_client():
        return mock_mongodb_client
    
    monkeypatch.setattr(
        'tradingagents.dataflows.cache.app_adapter.get_mongodb_client',
        mock_get_client
    )
    
    from tradingagents.dataflows.optimized_china_data import OptimizedChinaDataProvider
    
    provider = OptimizedChinaDataProvider()
    result = provider._get_cached_raw_financial_data("601985")
    
    # 应返回数据
    assert result is not None, "缓存加载器应返回数据"
    
    # 应包含各类报表
    assert 'income_statement' in result, "应包含利润表"
    assert 'balance_sheet' in result, "应包含资产负债表"
    assert 'cash_flow' in result, "应包含现金流量表"
    assert 'main_indicators' in result, "应包含财务指标"
    
    # 验证报表数据不为空
    assert len(result['income_statement']) > 0, "利润表不应为空"
    assert len(result['balance_sheet']) > 0, "资产负债表不应为空"
    assert len(result['main_indicators']) > 0, "财务指标不应为空"
    
    # 验证至少有一个 1231 年报期
    annual_periods = [
        record for record in result['income_statement'] 
        if str(record.get('report_period', '')).endswith('1231')
    ]
    assert len(annual_periods) >= 1, f"应至少有 1 个年报期，实际 {len(annual_periods)}"


def test_tools_can_read_akshare_data(monkeypatch, mock_mongodb_client, akshare_financial_document):
    """测试工具能正确读取 AkShare 数据"""
    # Mock get_mongodb_client
    def mock_get_client():
        return mock_mongodb_client
    
    monkeypatch.setattr(
        'tradingagents.dataflows.cache.app_adapter.get_mongodb_client',
        mock_get_client
    )
    
    from core.tools.implementations.fundamentals.stock_fundamentals import _load_recent_financial_data
    
    # 加载财务数据
    financial_data = _load_recent_financial_data("601985", limit=4)
    
    # 验证数据源
    assert financial_data['data_source'] == 'optimized_cache', f"数据源应为 optimized_cache，实际 {financial_data['data_source']}"
    
    # 验证包含各类报表
    assert len(financial_data['income_statement']) > 0, "利润表不应为空"
    assert len(financial_data['balance_sheet']) > 0, "资产负债表不应为空"
    assert len(financial_data['financial_indicators']) > 0, "财务指标不应为空"
    
    # 验证至少有一个年报期
    income_annual = [r for r in financial_data['income_statement'] if str(r.get('end_date', '')).endswith('1231')]
    assert len(income_annual) >= 1, f"利润表应至少有 1 个年报期，实际 {len(income_annual)}"


def test_aggregate_periods_preserves_data():
    """测试 _aggregate_periods_to_financial_data 正确聚合数据"""
    from tradingagents.dataflows.optimized_china_data import OptimizedChinaDataProvider
    
    provider = OptimizedChinaDataProvider()
    
    # 模拟展开后的期间记录
    periods = [
        {
            "report_period": "20251231",
            "report_date": "20251231",
            "ann_date": "20260320",
            "raw_data": {
                "income_statement": {
                    "revenue": 120000000000.0,
                    "net_income": 15000000000.0,
                },
                "balance_sheet": {
                    "total_assets": 500000000000.0,
                    "total_liab": 300000000000.0,
                },
                "cashflow_statement": {
                    "n_cashflow_act": 25000000000.0,
                },
                "financial_indicators": {
                    "roe": 7.5,
                    "debt_to_assets": 60.0,
                }
            }
        },
        {
            "report_period": "20250930",
            "report_date": "20250930",
            "ann_date": "20251030",
            "raw_data": {
                "income_statement": {
                    "revenue": 90000000000.0,
                    "net_income": 11000000000.0,
                },
                "balance_sheet": {
                    "total_assets": 480000000000.0,
                    "total_liab": 290000000000.0,
                },
                "cashflow_statement": {
                    "n_cashflow_act": 18000000000.0,
                },
                "financial_indicators": {
                    "roe": 5.8,
                    "debt_to_assets": 60.4,
                }
            }
        }
    ]
    
    result = provider._aggregate_periods_to_financial_data(periods)
    
    # 验证返回结构
    assert 'income_statement' in result
    assert 'balance_sheet' in result
    assert 'cash_flow' in result
    assert 'main_indicators' in result
    
    # 验证数据量
    assert len(result['income_statement']) == 2
    assert len(result['balance_sheet']) == 2
    assert len(result['cash_flow']) == 2
    assert len(result['main_indicators']) == 2
    
    # 验证第一期数据
    first_income = result['income_statement'][0]
    assert first_income['report_period'] == "20251231"
    assert first_income['revenue'] == 120000000000.0
    assert first_income['net_income'] == 15000000000.0
    
    first_balance = result['balance_sheet'][0]
    assert first_balance['total_assets'] == 500000000000.0
    assert first_balance['total_liab'] == 300000000000.0
    
    first_cashflow = result['cash_flow'][0]
    assert first_cashflow['n_cashflow_act'] == 25000000000.0
    
    first_indicators = result['main_indicators'][0]
    assert first_indicators['roe'] == 7.5
    assert first_indicators['debt_to_assets'] == 60.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
