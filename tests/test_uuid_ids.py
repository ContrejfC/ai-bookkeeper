"""Test UUID-based ID generation."""
import sys
import uuid
import re
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ingest.csv_parser import parse_csv_statement


def test_uuid_format():
    """Test that generated UUIDs are valid 32-character hex strings."""
    # Generate 100 UUIDs
    uuids = [uuid.uuid4().hex for _ in range(100)]
    
    # All should be 32 characters
    assert all(len(uid) == 32 for uid in uuids), "All UUIDs should be 32 chars"
    
    # All should be hex (0-9, a-f)
    hex_pattern = re.compile(r'^[0-9a-f]{32}$')
    assert all(hex_pattern.match(uid) for uid in uuids), "All UUIDs should be hex"


def test_uuid_uniqueness():
    """Test that 10,000 UUIDs are all unique."""
    uuids = [uuid.uuid4().hex for _ in range(10000)]
    assert len(set(uuids)) == 10000, "All 10k UUIDs should be unique"


def test_transaction_id_format():
    """Test that transaction IDs from CSV parser follow UUID format."""
    # Create a small test CSV
    test_csv = Path(__file__).parent.parent / "data" / "test_uuid_txn.csv"
    test_csv.parent.mkdir(parents=True, exist_ok=True)
    
    with open(test_csv, 'w') as f:
        f.write("date,amount,description,counterparty,currency\n")
        f.write("2025-01-01,100.50,Test Transaction,Test Vendor,USD\n")
        f.write("2025-01-02,-50.25,Another Test,Another Vendor,USD\n")
    
    try:
        transactions = parse_csv_statement(str(test_csv))
        
        # Check that txn_ids are in format "txn_<uuid>"
        for txn in transactions:
            assert txn.txn_id.startswith("txn_"), f"ID should start with 'txn_': {txn.txn_id}"
            
            # Extract the UUID part
            uuid_part = txn.txn_id[4:]  # Remove "txn_" prefix
            assert len(uuid_part) == 32, f"UUID part should be 32 chars: {uuid_part}"
            
            # Should be valid hex
            hex_pattern = re.compile(r'^[0-9a-f]{32}$')
            assert hex_pattern.match(uuid_part), f"UUID should be hex: {uuid_part}"
        
        # Both IDs should be different
        assert transactions[0].txn_id != transactions[1].txn_id, "Transaction IDs should be unique"
    
    finally:
        # Clean up test file
        if test_csv.exists():
            test_csv.unlink()


def test_je_id_format():
    """Test journal entry ID format with UUID."""
    # Generate mock JE IDs like the ingestion script does
    company_id = "test_company"
    je_ids = [f"je_{company_id}_{uuid.uuid4().hex[:16]}" for _ in range(100)]
    
    # Check format
    for je_id in je_ids:
        assert je_id.startswith(f"je_{company_id}_"), f"JE ID should start with prefix: {je_id}"
        uuid_part = je_id.split('_')[-1]
        assert len(uuid_part) == 16, f"UUID part should be 16 chars: {uuid_part}"
        
        hex_pattern = re.compile(r'^[0-9a-f]{16}$')
        assert hex_pattern.match(uuid_part), f"UUID part should be hex: {uuid_part}"
    
    # All should be unique
    assert len(set(je_ids)) == 100, "All 100 JE IDs should be unique"


if __name__ == "__main__":
    test_uuid_format()
    test_uuid_uniqueness()
    test_transaction_id_format()
    test_je_id_format()
    print("✅ All UUID ID tests passed!")

