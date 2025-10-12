"""
Tests for Xero Export (Sprint 11.2)

Tests idempotency, balanced totals, concurrency, and CSV output.
"""
import pytest
import threading
import hashlib
from decimal import Decimal
from datetime import datetime

from app.exporters.xero_exporter import XeroExporter, get_xero_credentials
from app.db.session import SessionLocal
from app.db.models import XeroMappingDB, XeroExportLogDB


@pytest.fixture
def db():
    """Database session."""
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def setup_mappings(db):
    """Set up test account mappings."""
    tenant_id = "test-tenant"
    
    # Clear existing
    db.query(XeroMappingDB).filter_by(tenant_id=tenant_id).delete()
    db.query(XeroExportLogDB).filter_by(tenant_id=tenant_id).delete()
    db.commit()
    
    # Add mappings
    mappings = [
        XeroMappingDB(tenant_id=tenant_id, internal_account="4000", xero_account_code="200", xero_account_name="Sales"),
        XeroMappingDB(tenant_id=tenant_id, internal_account="1000", xero_account_code="090", xero_account_name="Accounts Receivable"),
        XeroMappingDB(tenant_id=tenant_id, internal_account="5000", xero_account_code="400", xero_account_name="Advertising"),
    ]
    
    for mapping in mappings:
        db.add(mapping)
    
    db.commit()
    
    yield tenant_id
    
    # Cleanup
    db.query(XeroMappingDB).filter_by(tenant_id=tenant_id).delete()
    db.query(XeroExportLogDB).filter_by(tenant_id=tenant_id).delete()
    db.commit()


def create_test_je(je_id="test-je-001", txn_id="txn-001", balanced=True):
    """Create a test journal entry."""
    if balanced:
        lines = [
            {"account": "4000", "description": "Sales", "amount": -100.00},  # Credit
            {"account": "1000", "description": "AR", "amount": 100.00},  # Debit
        ]
    else:
        lines = [
            {"account": "4000", "description": "Sales", "amount": -100.00},
            {"account": "1000", "description": "AR", "amount": 90.00},  # Imbalanced
        ]
    
    return {
        "id": je_id,
        "txn_id": txn_id,
        "date": "2024-10-11",
        "memo": "Test journal entry",
        "lines": lines,
        "total_amount": sum(line['amount'] for line in lines)
    }


def test_idempotent_export_skips_duplicates(setup_mappings):
    """Test repeated export skips already-posted entries."""
    tenant_id = setup_mappings
    credentials = {"access_token": "mock", "xero_tenant_id": f"xero-{tenant_id}", "mock_mode": True}
    
    exporter = XeroExporter(tenant_id, credentials)
    je = create_test_je()
    
    # First export - should post
    result1 = exporter.export_journal_entry(je)
    assert result1["status"] == "posted"
    assert "external_id" in result1
    assert "xero_journal_id" in result1
    
    # Second export - should skip
    result2 = exporter.export_journal_entry(je)
    assert result2["status"] == "skipped"
    assert result2["reason"] == "already_exported"
    assert result2["external_id"] == result1["external_id"]
    
    print(f"✅ Idempotency test passed: posted → skipped")


def test_balanced_totals_enforced(setup_mappings):
    """Test journal entry must balance (debits == credits)."""
    tenant_id = setup_mappings
    credentials = {"access_token": "mock", "xero_tenant_id": f"xero-{tenant_id}"}
    
    exporter = XeroExporter(tenant_id, credentials)
    je_unbalanced = create_test_je(balanced=False)
    
    with pytest.raises(ValueError, match="not balanced"):
        exporter.export_journal_entry(je_unbalanced)
    
    print("✅ Balanced totals enforced")


def test_concurrency_safe_exports(setup_mappings):
    """Test concurrent exports handle race conditions (10 workers)."""
    tenant_id = setup_mappings
    credentials = {"access_token": "mock", "xero_tenant_id": f"xero-{tenant_id}"}
    
    je = create_test_je(je_id="concurrent-je-001", txn_id="concurrent-txn-001")
    
    results = []
    errors = []
    
    def export_worker():
        try:
            exporter = XeroExporter(tenant_id, credentials)
            result = exporter.export_journal_entry(je)
            results.append(result)
        except Exception as e:
            errors.append(str(e))
    
    # Start 10 concurrent exports
    threads = []
    for i in range(10):
        t = threading.Thread(target=export_worker)
        threads.append(t)
        t.start()
    
    # Wait for all
    for t in threads:
        t.join()
    
    # Check results
    assert len(results) == 10, "All exports should complete"
    
    statuses = [r["status"] for r in results]
    posted_count = statuses.count("posted")
    skipped_count = statuses.count("skipped")
    
    # At least one should post, rest should skip
    assert posted_count >= 1, "At least one export should post"
    assert skipped_count >= 8, "Most exports should skip (race condition)"
    assert posted_count + skipped_count == 10, "All should post or skip"
    
    print(f"✅ Concurrency test: {posted_count} posted, {skipped_count} skipped (safe)")


def test_account_mapping_required(setup_mappings):
    """Test export fails gracefully if account mapping missing."""
    tenant_id = setup_mappings
    credentials = {"access_token": "mock", "xero_tenant_id": f"xero-{tenant_id}"}
    
    exporter = XeroExporter(tenant_id, credentials)
    
    # JE with unmapped account
    je = {
        "id": "test-unmapped",
        "txn_id": "txn-unmapped",
        "date": "2024-10-11",
        "memo": "Test",
        "lines": [
            {"account": "9999", "description": "Unmapped", "amount": -100.00},  # Not mapped
            {"account": "1000", "description": "AR", "amount": 100.00},
        ],
        "total_amount": 0
    }
    
    with pytest.raises(ValueError, match="No Xero mapping"):
        exporter.export_journal_entry(je)
    
    print("✅ Missing account mapping detected")


def test_sample_csv_export(setup_mappings):
    """Test CSV export format matches sample."""
    tenant_id = setup_mappings
    credentials = {"access_token": "mock", "xero_tenant_id": f"xero-{tenant_id}"}
    
    exporter = XeroExporter(tenant_id, credentials)
    
    # Export multiple JEs
    jes = [
        create_test_je(je_id=f"je-{i}", txn_id=f"txn-{i}")
        for i in range(3)
    ]
    
    results = []
    for je in jes:
        result = exporter.export_journal_entry(je)
        results.append(result)
    
    # Generate CSV
    import csv
    import os
    
    os.makedirs("artifacts/export", exist_ok=True)
    csv_path = "artifacts/export/sample_xero_export.csv"
    
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["journal_entry_id", "external_id", "xero_journal_id", "status", "date"])
        writer.writeheader()
        
        for je, result in zip(jes, results):
            writer.writerow({
                "journal_entry_id": je["id"],
                "external_id": result["external_id"],
                "xero_journal_id": result.get("xero_journal_id", ""),
                "status": result["status"],
                "date": je["date"]
            })
    
    # Verify CSV exists and has data
    assert os.path.exists(csv_path)
    
    with open(csv_path, "r") as f:
        lines = f.readlines()
        assert len(lines) == 4  # Header + 3 rows
    
    print(f"✅ Sample CSV exported: {csv_path}")


def test_external_id_generation():
    """Test external ID is deterministic and unique."""
    tenant_id = "test-tenant"
    credentials = {"mock_mode": True}
    
    exporter = XeroExporter(tenant_id, credentials)
    
    je1 = create_test_je(je_id="je-1", txn_id="txn-1")
    je2 = create_test_je(je_id="je-1", txn_id="txn-1")  # Same as je1
    je3 = create_test_je(je_id="je-2", txn_id="txn-2")  # Different
    
    ext_id_1 = exporter._generate_external_id(je1)
    ext_id_2 = exporter._generate_external_id(je2)
    ext_id_3 = exporter._generate_external_id(je3)
    
    # Same JE should produce same ID
    assert ext_id_1 == ext_id_2
    
    # Different JE should produce different ID
    assert ext_id_1 != ext_id_3
    
    # Format check
    assert ext_id_1.startswith("AIBK-")
    assert len(ext_id_1) == 33  # AIBK- + 28 hex chars
    
    print(f"✅ External ID generation: deterministic and unique")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

