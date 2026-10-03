"""
Test that AkShare financial data stored in MongoDB can be read by analyst tools.

Reproduces the symptom described:
- Mongo has a document with main_indicators as a wide table
- get_financial_statements and get_cash_flow_statement should return data
- DCF should see annual periods from 1231 columns
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.skill_runtime.data_access import expand_financial_document_to_periods


def test_expand_akshare_wide_table_to_periods():
    """Test that AkShare main_indicators wide table is expanded to period records."""
    
    # Simulate an AkShare document as stored in MongoDB
    akshare_doc = {
        "code": "601985",
        "symbol": "601985",
        "full_symbol": "601985.SH",
        "market": "CN",
        "report_period": "20260630",
        "report_type": "quarterly",
        "data_source": "akshare",
        "ann_date": "",
        # Flat scalar fields copied from wide table
        "revenue": 6543210000.0,
        "net_income": 1234567000.0,
        "roe": 12.5,
        "debt_to_assets": 45.3,
        "raw_data": {
            "main_indicators": [
                {"指标": "营业总收入", "20260630": 6543210000.0, "20260331": 3210000000.0, "20251231": 12345678000.0},
                {"指标": "归母净利润", "20260630": 1234567000.0, "20260331": 567890000.0, "20251231": 2345678000.0},
                {"指标": "净利润", "20260630": 1234567000.0, "20260331": 567890000.0, "20251231": 2345678000.0},
                {"指标": "经营活动产生的现金流量净额", "20260630": 987654000.0, "20260331": 456789000.0, "20251231": 1876543000.0},
                {"指标": "总资产", "20260630": 98765432000.0, "20260331": 95000000000.0, "20251231": 92000000000.0},
                {"指标": "股东权益合计(净资产)", "20260630": 54321098000.0, "20260331": 52000000000.0, "20251231": 50000000000.0},
                {"指标": "净资产收益率_平均", "20260630": 12.5, "20260331": 11.8, "20251231": 24.7},
                {"指标": "资产负债率", "20260630": 45.3, "20260331": 45.5, "20251231": 45.7},
            ],
        }
    }
    
    periods = expand_financial_document_to_periods(akshare_doc)
    
    # Should expand to 3 periods: Q2 2026, Q1 2026, annual 2025
    assert len(periods) >= 3, f"Expected at least 3 periods, got {len(periods)}"
    
    # Sort by period descending to get latest first
    periods_by_date = {p["report_period"]: p for p in periods}
    
    # Check Q2 2026 data
    assert "20260630" in periods_by_date
    q2_2026 = periods_by_date["20260630"]
    assert q2_2026["revenue"] == 6543210000.0, f"Q2 revenue mismatch: {q2_2026.get('revenue')}"
    assert q2_2026["net_income"] == 1234567000.0 or q2_2026["net_profit"] == 1234567000.0
    assert q2_2026["n_cashflow_act"] == 987654000.0, f"Q2 operating cashflow mismatch: {q2_2026.get('n_cashflow_act')}"
    assert q2_2026["roe"] == 12.5
    assert q2_2026["debt_to_assets"] == 45.3
    
    # Check annual 2025 (should be detected as annual)
    assert "20251231" in periods_by_date
    annual_2025 = periods_by_date["20251231"]
    assert annual_2025["report_type"] == "annual", f"2025 should be annual, got {annual_2025['report_type']}"
    assert annual_2025["revenue"] == 12345678000.0
    assert annual_2025["net_profit"] == 2345678000.0 or annual_2025["net_income"] == 2345678000.0
    assert annual_2025["n_cashflow_act"] == 1876543000.0


def test_akshare_metric_name_mapping():
    """Test that Chinese metric names in main_indicators are mapped correctly."""
    
    akshare_doc = {
        "code": "600519",
        "symbol": "600519",
        "report_period": "20260630",
        "data_source": "akshare",
        "raw_data": {
            "main_indicators": [
                # Revenue variations
                {"指标": "营业总收入", "20260630": 100000.0},
                {"指标": "营业收入", "20260630": 100000.0},
                # Net profit variations
                {"指标": "归母净利润", "20260630": 20000.0},
                {"指标": "净利润", "20260630": 20000.0},
                # Cash flow variations
                {"指标": "经营活动产生的现金流量净额", "20260630": 15000.0},
                {"指标": "投资活动产生的现金流量净额", "20260630": -5000.0},
                {"指标": "筹资活动产生的现金流量净额", "20260630": -3000.0},
                # Balance sheet
                {"指标": "总资产", "20260630": 500000.0},
                {"指标": "负债合计", "20260630": 200000.0},
                {"指标": "股东权益合计(净资产)", "20260630": 300000.0},
                # Ratios
                {"指标": "净资产收益率_平均", "20260630": 15.5},
                {"指标": "净资产收益率(ROE)", "20260630": 15.5},
                {"指标": "资产负债率", "20260630": 40.0},
                {"指标": "负债率", "20260630": 40.0},
            ],
        }
    }
    
    periods = expand_financial_document_to_periods(akshare_doc)
    assert len(periods) > 0
    
    period = periods[0]
    assert period["revenue"] == 100000.0 or period["oper_rev"] == 100000.0
    assert period["net_profit"] == 20000.0 or period["net_income"] == 20000.0
    assert period["n_cashflow_act"] == 15000.0
    assert period["n_cashflow_inv_act"] == -5000.0
    assert period["n_cashflow_fin_act"] == -3000.0
    assert period["total_assets"] == 500000.0
    assert period["total_liab"] == 200000.0
    assert period["total_equity"] == 300000.0
    assert period["roe"] == 15.5
    assert period["debt_to_assets"] == 40.0


def test_akshare_multiple_annual_periods_for_dcf():
    """Test that DCF can see multiple annual periods from main_indicators."""
    
    akshare_doc = {
        "code": "600519",
        "symbol": "600519",
        "report_period": "20261231",
        "data_source": "akshare",
        "raw_data": {
            "main_indicators": [
                {"指标": "营业总收入", 
                 "20261231": 500000000.0,
                 "20251231": 450000000.0,
                 "20241231": 400000000.0,
                 "20231231": 350000000.0,
                 "20221231": 300000000.0},
                {"指标": "归母净利润",
                 "20261231": 100000000.0,
                 "20251231": 90000000.0,
                 "20241231": 80000000.0,
                 "20231231": 70000000.0,
                 "20221231": 60000000.0},
            ],
        }
    }
    
    periods = expand_financial_document_to_periods(akshare_doc)
    
    # Should have at least 5 annual periods
    annual_periods = [p for p in periods if p.get("report_type") == "annual"]
    assert len(annual_periods) >= 5, f"Expected at least 5 annual periods, got {len(annual_periods)}"
    
    # Check that all are 1231 dates
    for p in annual_periods:
        assert p["report_period"].endswith("1231"), f"Annual period should end in 1231: {p['report_period']}"
    
    # Verify revenue trend
    periods_by_date = {p["report_period"]: p for p in annual_periods}
    assert periods_by_date["20261231"]["revenue"] == 500000000.0
    assert periods_by_date["20251231"]["revenue"] == 450000000.0
    assert periods_by_date["20241231"]["revenue"] == 400000000.0


def test_mixed_tushare_and_akshare_structure():
    """Test that documents with both Tushare-style and AkShare-style data work."""
    
    mixed_doc = {
        "code": "601985",
        "symbol": "601985",
        "report_period": "20260630",
        "data_source": "akshare",
        "revenue": 6543210000.0,
        "raw_data": {
            # Tushare-style statements (should still work)
            "income_statement": [
                {"end_date": "20260630", "revenue": 6543210000.0, "n_income_attr_p": 1234567000.0},
            ],
            # AkShare-style main_indicators (should also work)
            "main_indicators": [
                {"指标": "经营活动产生的现金流量净额", "20260630": 987654000.0},
            ],
        }
    }
    
    periods = expand_financial_document_to_periods(mixed_doc)
    assert len(periods) > 0
    
    period = periods[0]
    # Should have data from both sources
    assert period["revenue"] == 6543210000.0
    assert period["net_profit"] == 1234567000.0
    assert period["n_cashflow_act"] == 987654000.0


if __name__ == "__main__":
    # Run tests directly for debugging
    test_expand_akshare_wide_table_to_periods()
    test_akshare_metric_name_mapping()
    test_akshare_multiple_annual_periods_for_dcf()
    test_mixed_tushare_and_akshare_structure()
    print("All tests passed!")
