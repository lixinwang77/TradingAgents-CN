"""
Integration test simulating the actual use case described in the issue.

Tests that financial tools can read AkShare data from MongoDB-like cache.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.skill_runtime.data_access import expand_financial_document_to_periods


def test_complete_akshare_601985_scenario():
    """
    Reproduce the exact scenario from the issue:
    - Symbol 601985 (中国核电)
    - data_source=akshare
    - report_period 20260630
    - Flat scalars AND raw_data.main_indicators as wide table
    - NO income_statement/balance_sheet/cashflow_statement
    """
    
    # This is what's actually stored in MongoDB for 601985
    mongo_document = {
        "code": "601985",
        "symbol": "601985",
        "full_symbol": "601985.SH",
        "market": "CN",
        "report_period": "20260630",
        "report_type": "quarterly",
        "data_source": "akshare",
        "name": "中国核电",
        # Flat scalar fields extracted from wide table
        "revenue": 6543210000.0,
        "net_income": 1234567000.0,
        "roe": 12.5,
        "debt_to_assets": 45.3,
        # The actual raw_data structure from AkShare
        "raw_data": {
            "main_indicators": [
                {
                    "选项": "主要指标",
                    "指标": "营业总收入",
                    "20260630": 6543210000.0,
                    "20260331": 3210000000.0,
                    "20251231": 12345678000.0,
                    "20250930": 9000000000.0
                },
                {
                    "选项": "主要指标",
                    "指标": "归母净利润",
                    "20260630": 1234567000.0,
                    "20260331": 567890000.0,
                    "20251231": 2345678000.0,
                    "20250930": 1800000000.0
                },
                {
                    "选项": "主要指标",
                    "指标": "净利润",
                    "20260630": 1234567000.0,
                    "20260331": 567890000.0,
                    "20251231": 2345678000.0,
                    "20250930": 1800000000.0
                },
                {
                    "选项": "主要指标",
                    "指标": "经营活动产生的现金流量净额",
                    "20260630": 987654000.0,
                    "20260331": 456789000.0,
                    "20251231": 1876543000.0,
                    "20250930": 1400000000.0
                },
                {
                    "选项": "主要指标",
                    "指标": "总资产",
                    "20260630": 98765432000.0,
                    "20260331": 95000000000.0,
                    "20251231": 92000000000.0,
                    "20250930": 93000000000.0
                },
                {
                    "选项": "主要指标",
                    "指标": "股东权益合计(净资产)",
                    "20260630": 54321098000.0,
                    "20260331": 52000000000.0,
                    "20251231": 50000000000.0,
                    "20250930": 51000000000.0
                },
                {
                    "选项": "主要指标",
                    "指标": "净资产收益率_平均",
                    "20260630": 12.5,
                    "20260331": 11.8,
                    "20251231": 24.7,
                    "20250930": 20.2
                },
                {
                    "选项": "主要指标",
                    "指标": "资产负债率",
                    "20260630": 45.3,
                    "20260331": 45.5,
                    "20251231": 45.7,
                    "20250930": 45.4
                },
            ]
            # NOTE: No income_statement, balance_sheet, or cashflow_statement keys
        }
    }
    
    # Expand to period records (what financial tools will see)
    periods = expand_financial_document_to_periods(mongo_document)
    
    # Verify we got all 4 periods
    assert len(periods) == 4, f"Expected 4 periods, got {len(periods)}"
    
    periods_by_date = {p["report_period"]: p for p in periods}
    
    # Test 1: get_financial_statements for 2026-06-30
    q2_2026 = periods_by_date["20260630"]
    print(f"✓ Q2 2026 data found: {q2_2026['report_period']}")
    
    # Check revenue (should come from income_statement section)
    assert q2_2026["revenue"] == 6543210000.0, f"Revenue mismatch: {q2_2026['revenue']}"
    print(f"  ✓ Revenue: {q2_2026['revenue']:,.0f}")
    
    # Check net income (should come from income_statement section)
    assert q2_2026["net_profit"] == 1234567000.0, f"Net profit mismatch: {q2_2026['net_profit']}"
    print(f"  ✓ Net Profit: {q2_2026['net_profit']:,.0f}")
    
    # Check ROE (should come from financial_indicators section)
    assert q2_2026["roe"] == 12.5, f"ROE mismatch: {q2_2026['roe']}"
    print(f"  ✓ ROE: {q2_2026['roe']}%")
    
    # Check debt ratio (should come from financial_indicators section)
    assert q2_2026["debt_to_assets"] == 45.3, f"Debt ratio mismatch: {q2_2026['debt_to_assets']}"
    print(f"  ✓ Debt to Assets: {q2_2026['debt_to_assets']}%")
    
    # Test 2: get_cash_flow_statement for 2026-06-30
    # Operating cash flow should be available
    assert q2_2026["n_cashflow_act"] == 987654000.0, f"Operating cashflow mismatch: {q2_2026['n_cashflow_act']}"
    print(f"  ✓ Operating Cash Flow: {q2_2026['n_cashflow_act']:,.0f}")
    
    # Investment and financing cash flow should NOT be present (not in wide table)
    assert q2_2026.get("n_cashflow_inv_act") is None, "Investment cashflow should be absent"
    assert q2_2026.get("n_cashflow_fin_act") is None, "Financing cashflow should be absent"
    print(f"  ✓ Investment/Financing CF correctly absent (not in source data)")
    
    # Test 3: DCF should see annual periods (1231 columns)
    annual_2025 = periods_by_date["20251231"]
    assert annual_2025["report_type"] == "annual", f"Should be annual: {annual_2025['report_type']}"
    assert annual_2025["report_period"] == "20251231"
    assert annual_2025["revenue"] == 12345678000.0
    print(f"✓ Annual 2025 found: {annual_2025['report_period']}")
    print(f"  ✓ Report Type: {annual_2025['report_type']}")
    print(f"  ✓ Revenue: {annual_2025['revenue']:,.0f}")
    
    # Count annual periods
    annual_periods = [p for p in periods if p["report_type"] == "annual"]
    print(f"✓ Found {len(annual_periods)} annual period(s) total")
    
    # Verify statements are structured correctly
    assert "income_statement" in q2_2026, "Should have income_statement section"
    assert "balance_sheet" in q2_2026, "Should have balance_sheet section"
    assert "cashflow_statement" in q2_2026, "Should have cashflow_statement section"
    assert "financial_indicators" in q2_2026, "Should have financial_indicators section"
    print(f"✓ All statement sections present in period records")
    
    # Verify statement fields are properly populated
    assert q2_2026["income_statement"]["revenue"] == 6543210000.0
    assert q2_2026["balance_sheet"]["total_assets"] == 98765432000.0
    assert q2_2026["cashflow_statement"]["n_cashflow_act"] == 987654000.0
    assert q2_2026["financial_indicators"]["roe"] == 12.5
    print(f"✓ Statement sections properly populated from wide table")
    
    print("\n✅ All integration tests passed!")
    print("   - get_financial_statements can read revenue, net income, ROE, debt ratio")
    print("   - get_cash_flow_statement can read operating cash flow")
    print("   - DCF can see annual periods from 1231 columns")
    print("   - Missing metrics (investment/financing CF) stay absent")


if __name__ == "__main__":
    test_complete_akshare_601985_scenario()
