#!/usr/bin/env python3
"""
Unit tests for QBO export idempotency (Sprint 9 Stage F).

Tests that re-exports skip duplicates based on ExternalId.
"""
import pytest
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))


class QBOExportManager:
    """Mock QBO export manager for testing."""
    
    def __init__(self):
        self.export_log = {}  # external_id -> metadata
        self.exported_lines = []
    
    def generate_external_id(self, je_id: str, date: str, lines: list) -> str:
        """
        Generate SHA-256 ExternalId for a journal entry.
        
        Args:
            je_id: Journal entry ID
            date: Transaction date
            lines: Sorted list of journal entry lines
            
        Returns:
            64-character hex SHA-256 hash
        """
        # Sort lines for consistency
        sorted_lines = sorted(lines, key=lambda x: (x['account'], x['debit'], x['credit']))
        lines_json = json.dumps(sorted_lines, sort_keys=True)
        
        # Create hash input
        hash_input = f"{je_id}|{date}|{lines_json}"
        
        # Generate SHA-256
        sha256_hash = hashlib.sha256(hash_input.encode()).hexdigest()
        
        return sha256_hash
    
    def export_to_csv(self, journal_entries: list) -> dict:
        """
        Export journal entries to QBO CSV format.
        
        Args:
            journal_entries: List of JE dicts
            
        Returns:
            Export result with counts
        """
        new_count = 0
        skipped_count = 0
        lines_exported = []
        
        for je in journal_entries:
            # Generate ExternalId
            external_id = self.generate_external_id(
                je['je_id'],
                je['date'],
                je['lines']
            )
            
            # Check if already exported
            if external_id in self.export_log:
                skipped_count += 1
                continue
            
            # Export lines
            for line in je['lines']:
                csv_line = {
                    'Date': je['date'],
                    'JournalNumber': je['je_id'],
                    'AccountName': line['account'],
                    'Debit': line.get('debit', 0.0),
                    'Credit': line.get('credit', 0.0),
                    'Currency': 'USD',
                    'Memo': je.get('memo', ''),
                    'Entity': je.get('entity', ''),
                    'Class': je.get('class', ''),
                    'Location': je.get('location', ''),
                    'ExternalId': external_id[:32]  # First 32 hex chars
                }
                lines_exported.append(csv_line)
            
            # Log export (store full 64-char hash internally)
            self.export_log[external_id] = {
                'je_id': je['je_id'],
                'export_date': je['date'],
                'line_count': len(je['lines']),
                'status': 'exported'
            }
            new_count += 1
        
        self.exported_lines.extend(lines_exported)
        
        return {
            'new': new_count,
            'skipped': skipped_count,
            'total_lines': len(lines_exported)
        }
    
    def get_exported_lines(self) -> list:
        """Get all exported CSV lines."""
        return self.exported_lines


class TestQBOIdempotency:
    """Test QBO export idempotency."""
    
    @pytest.fixture
    def manager(self):
        """Create a fresh export manager."""
        return QBOExportManager()
    
    @pytest.fixture
    def sample_jes(self):
        """Sample journal entries."""
        return [
            {
                'je_id': 'JE-2024-001',
                'date': '2024-10-10',
                'memo': 'Office supplies',
                'lines': [
                    {'account': '6000 Supplies', 'debit': 234.56, 'credit': 0.0},
                    {'account': '1000 Checking', 'debit': 0.0, 'credit': 234.56}
                ]
            },
            {
                'je_id': 'JE-2024-002',
                'date': '2024-10-09',
                'memo': 'Revenue',
                'lines': [
                    {'account': '1000 Checking', 'debit': 1250.0, 'credit': 0.0},
                    {'account': '8000 Revenue', 'debit': 0.0, 'credit': 1250.0}
                ]
            }
        ]
    
    def test_reexport_skips_dupes(self, manager, sample_jes):
        """
        CRITICAL TEST: Re-export skips duplicates.
        
        This ensures idempotency - exporting the same JEs twice
        should not create duplicate lines in QBO.
        """
        # First export
        result1 = manager.export_to_csv(sample_jes)
        
        assert result1['new'] == 2, "Should export 2 new JEs"
        assert result1['skipped'] == 0, "Should skip 0 on first run"
        assert result1['total_lines'] == 4, "Should export 4 lines (2 per JE)"
        
        # Re-export same JEs
        result2 = manager.export_to_csv(sample_jes)
        
        assert result2['new'] == 0, "Should export 0 new JEs on re-run"
        assert result2['skipped'] == 2, "Should skip 2 duplicates"
        assert result2['total_lines'] == 0, "Should export 0 lines (all skipped)"
        
        # Verify total lines in export
        all_lines = manager.get_exported_lines()
        assert len(all_lines) == 4, "Should have exactly 4 lines total (no dupes)"
        
        print(f"\n✅ Idempotency test passed:")
        print(f"   First export: {result1['new']} new, {result1['skipped']} skipped")
        print(f"   Re-export: {result2['new']} new, {result2['skipped']} skipped")
        print(f"   Total lines: {len(all_lines)} (no duplicates)")
    
    def test_external_id_deterministic(self, manager):
        """Test that ExternalId is deterministic for same JE."""
        je = {
            'je_id': 'JE-2024-001',
            'date': '2024-10-10',
            'lines': [
                {'account': '6000 Supplies', 'debit': 100.0, 'credit': 0.0},
                {'account': '1000 Checking', 'debit': 0.0, 'credit': 100.0}
            ]
        }
        
        # Generate ExternalId twice
        id1 = manager.generate_external_id(je['je_id'], je['date'], je['lines'])
        id2 = manager.generate_external_id(je['je_id'], je['date'], je['lines'])
        
        assert id1 == id2, "ExternalId should be deterministic"
        assert len(id1) == 64, "SHA-256 should be 64 hex chars"
        
        print(f"\n✅ ExternalId is deterministic:")
        print(f"   Full hash: {id1}")
        print(f"   CSV value (first 32): {id1[:32]}")
    
    def test_external_id_unique_for_different_jes(self, manager):
        """Test that different JEs get different ExternalIds."""
        je1 = {
            'je_id': 'JE-2024-001',
            'date': '2024-10-10',
            'lines': [
                {'account': '6000 Supplies', 'debit': 100.0, 'credit': 0.0},
                {'account': '1000 Checking', 'debit': 0.0, 'credit': 100.0}
            ]
        }
        
        je2 = {
            'je_id': 'JE-2024-002',
            'date': '2024-10-10',
            'lines': [
                {'account': '6000 Supplies', 'debit': 100.0, 'credit': 0.0},
                {'account': '1000 Checking', 'debit': 0.0, 'credit': 100.0}
            ]
        }
        
        id1 = manager.generate_external_id(je1['je_id'], je1['date'], je1['lines'])
        id2 = manager.generate_external_id(je2['je_id'], je2['date'], je2['lines'])
        
        assert id1 != id2, "Different JEs should have different ExternalIds"
        
        print(f"\n✅ Different JEs get unique ExternalIds:")
        print(f"   JE-001: {id1[:32]}...")
        print(f"   JE-002: {id2[:32]}...")
    
    def test_line_order_normalized(self, manager):
        """Test that line order doesn't affect ExternalId."""
        je1 = {
            'je_id': 'JE-2024-001',
            'date': '2024-10-10',
            'lines': [
                {'account': '6000 Supplies', 'debit': 100.0, 'credit': 0.0},
                {'account': '1000 Checking', 'debit': 0.0, 'credit': 100.0}
            ]
        }
        
        je2 = {
            'je_id': 'JE-2024-001',
            'date': '2024-10-10',
            'lines': [
                {'account': '1000 Checking', 'debit': 0.0, 'credit': 100.0},
                {'account': '6000 Supplies', 'debit': 100.0, 'credit': 0.0}
            ]
        }
        
        id1 = manager.generate_external_id(je1['je_id'], je1['date'], je1['lines'])
        id2 = manager.generate_external_id(je2['je_id'], je2['date'], je2['lines'])
        
        assert id1 == id2, "Line order should not affect ExternalId (normalized)"
        
        print(f"\n✅ Line order is normalized:")
        print(f"   Both orders produce same ExternalId: {id1[:32]}...")
    
    def test_mixed_new_and_duplicate_jes(self, manager, sample_jes):
        """Test export with mix of new and duplicate JEs."""
        # Export first JE
        result1 = manager.export_to_csv([sample_jes[0]])
        assert result1['new'] == 1
        assert result1['skipped'] == 0
        
        # Export both JEs (one new, one duplicate)
        result2 = manager.export_to_csv(sample_jes)
        assert result2['new'] == 1, "Should export 1 new JE"
        assert result2['skipped'] == 1, "Should skip 1 duplicate"
        
        # Verify total lines
        all_lines = manager.get_exported_lines()
        assert len(all_lines) == 4, "Should have 4 lines total (2 JEs × 2 lines)"
        
        print(f"\n✅ Mixed new/duplicate handling:")
        print(f"   First batch: {result1['new']} new")
        print(f"   Second batch: {result2['new']} new, {result2['skipped']} skipped")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

