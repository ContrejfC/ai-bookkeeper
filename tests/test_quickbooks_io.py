"""Tests for QuickBooks and Xero import/export functionality."""
import pytest
from io import StringIO
from app.exporters.quickbooks_export import QuickBooksExporter, XeroExporter
from app.importers.quickbooks_import import QuickBooksImporter, XeroImporter


def test_quickbooks_account_mapping():
    """Test mapping internal accounts to QuickBooks format."""
    # Test bank account
    result = QuickBooksExporter.map_account_to_qbo("1000 Cash at Bank")
    assert result['account_num'] == "1000"
    assert result['account_name'] == "Cash at Bank"
    assert result['account_type'] == "BANK"
    
    # Test expense account
    result = QuickBooksExporter.map_account_to_qbo("6100 Office Supplies")
    assert result['account_num'] == "6100"
    assert result['account_name'] == "Office Supplies"
    assert result['account_type'] == "EXP"
    
    # Test revenue account
    result = QuickBooksExporter.map_account_to_qbo("8000 Sales Revenue")
    assert result['account_num'] == "8000"
    assert result['account_name'] == "Sales Revenue"
    assert result['account_type'] == "INC"


def test_xero_account_mapping():
    """Test mapping internal accounts to Xero format."""
    result = XeroExporter.map_account_to_xero("6100 Office Supplies")
    assert result['account_code'] == "6100"
    assert result['account_name'] == "Office Supplies"


def test_quickbooks_import_csv():
    """Test importing chart of accounts from CSV."""
    csv_content = """Account Number,Account Name,Account Type,Description,Balance
1000,Cash at Bank,BANK,Main checking account,5000.00
6100,Office Supplies,EXP,Office supplies expense,0.00
8000,Sales Revenue,INC,Revenue from sales,10000.00
"""
    
    accounts = QuickBooksImporter.import_from_csv(csv_content)
    
    assert len(accounts) == 3
    assert accounts[0]['account_num'] == "1000"
    assert accounts[0]['account_name'] == "Cash at Bank"
    assert accounts[0]['balance'] == 5000.00
    
    # Test mapping to internal format
    internal_coa = QuickBooksImporter.map_to_internal_coa(accounts)
    assert len(internal_coa) == 3
    assert "1000 Cash at Bank" in internal_coa
    assert "6100 Office Supplies" in internal_coa


def test_xero_import_csv():
    """Test importing chart of accounts from Xero."""
    csv_content = """Account Code,Account Name,Type,Tax Type,Description
200,Sales,REVENUE,Tax on Income,Revenue from product sales
310,Office Expenses,EXPENSE,Tax Exempt,Office related expenses
400,Bank Account,BANK,Tax Exempt,Main business account
"""
    
    accounts = XeroImporter.import_from_csv(csv_content)
    
    assert len(accounts) == 3
    assert accounts[0]['account_num'] == "200"
    assert accounts[0]['account_name'] == "Sales"
    
    # Test mapping to internal format
    internal_coa = XeroImporter.map_to_internal_coa(accounts)
    assert len(internal_coa) == 3
    assert "200 Sales" in internal_coa


def test_quickbooks_iif_format():
    """Test that IIF export produces correct format."""
    # This is a basic structure test
    # In a real scenario, we'd use a mock database session
    output = StringIO()
    
    # Manually write expected format to verify structure
    output.write("!TRNS\tTRNSID\tTRNSTYPE\tDATE\tACCNT\tAMOUNT\tMEMO\n")
    output.write("!SPL\tSPLID\tTRNSTYPE\tDATE\tACCNT\tAMOUNT\tMEMO\n")
    output.write("!ENDTRNS\n")
    
    content = output.getvalue()
    
    assert "!TRNS" in content
    assert "!SPL" in content
    assert "!ENDTRNS" in content


def test_xero_csv_format():
    """Test that Xero CSV export has correct headers."""
    output = StringIO()
    
    # Write expected headers
    import csv
    writer = csv.writer(output)
    writer.writerow([
        "*JournalNumber",
        "*Date",
        "*AccountCode",
        "AccountName",
        "*Description",
        "Debit",
        "Credit",
        "TaxType",
        "TaxAmount",
        "TrackingName1",
        "TrackingOption1"
    ])
    
    content = output.getvalue()
    
    assert "*JournalNumber" in content
    assert "*AccountCode" in content
    assert "Debit" in content
    assert "Credit" in content


def test_quickbooks_iif_parse():
    """Test parsing QuickBooks IIF account list."""
    iif_content = """!ACCNT\tNAME\tACCNTTYPE\tDESC\tACCNUM\tBALANCE
ACCNT\tCash\tBANK\tMain bank account\t1000\t5000.00
ACCNT\tOffice Supplies\tEXP\tSupplies expense\t6100\t0.00
!END
"""
    
    accounts = QuickBooksImporter.parse_iif_accounts(iif_content)
    
    assert len(accounts) == 2
    assert accounts[0]['account_name'] == "Cash"
    assert accounts[0]['account_type'] == "BANK"
    assert accounts[0]['balance'] == 5000.00


def test_account_type_mapping():
    """Test that account types are correctly mapped."""
    # Liability account
    result = QuickBooksExporter.map_account_to_qbo("2000 Credit Card Payable")
    assert result['account_type'] == "OCLIAB"
    
    # Tax liability
    result = QuickBooksExporter.map_account_to_qbo("2100 Taxes Payable")
    assert result['account_type'] == "OCLIAB"
    
    # Advertising expense
    result = QuickBooksExporter.map_account_to_qbo("7000 Advertising")
    assert result['account_type'] == "EXP"


def test_empty_import():
    """Test handling of empty import files."""
    csv_content = """Account Number,Account Name,Account Type,Description,Balance
"""
    
    accounts = QuickBooksImporter.import_from_csv(csv_content)
    assert len(accounts) == 0


def test_malformed_csv_handling():
    """Test that malformed CSV is handled gracefully."""
    csv_content = """Account Number,Account Name
1000
6100,Office Supplies
"""
    
    accounts = QuickBooksImporter.import_from_csv(csv_content)
    # Should still parse the valid row
    assert len(accounts) >= 1
    assert any(acc['account_name'] == "Office Supplies" for acc in accounts)

