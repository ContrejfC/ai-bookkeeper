#!/usr/bin/env python3
"""
Unit tests for QBO export balanced totals (Sprint 9 Stage F).

Tests that exported CSVs maintain debit = credit balance.
"""
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.test_qbo_idempotency import QBOExportManager


class TestQBOBalancedTotals:
    """Test QBO export maintains balanced accounting."""
    
    @pytest.fixture
    def manager(self):
        """Create a fresh export manager."""
        return QBOExportManager()
    
    def test_debits_equal_credits(self, manager):
        """
        CRITICAL TEST: Exported CSV has balanced totals.
        
        This ensures accounting integrity - sum of debits must equal
        sum of credits across all exported lines.
        """
        sample_jes = [
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
            },
            {
                'je_id': 'JE-2024-003',
                'date': '2024-10-08',
                'memo': 'Multi-line expense',
                'lines': [
                    {'account': '6000 Supplies', 'debit': 100.0, 'credit': 0.0},
                    {'account': '6100 Office', 'debit': 50.0, 'credit': 0.0},
                    {'account': '1000 Checking', 'debit': 0.0, 'credit': 150.0}
                ]
            }
        ]
        
        # Export JEs
        result = manager.export_to_csv(sample_jes)
        
        # Get all lines
        all_lines = manager.get_exported_lines()
        
        # Calculate totals
        total_debit = sum(line['Debit'] for line in all_lines)
        total_credit = sum(line['Credit'] for line in all_lines)
        
        # Assertions
        assert result['new'] == 3, "Should export 3 JEs"
        assert len(all_lines) == 7, "Should have 7 total lines"
        
        # CRITICAL: Debits must equal credits
        assert total_debit == total_credit, \
            f"Debits ({total_debit}) must equal Credits ({total_credit})"
        
        # Additional precision check (accounting systems need exact match)
        balance_diff = abs(total_debit - total_credit)
        assert balance_diff < 0.01, \
            f"Balance difference ({balance_diff}) exceeds precision threshold"
        
        print(f"\n✅ Balanced totals test passed:")
        print(f"   Total Debit:  ${total_debit:,.2f}")
        print(f"   Total Credit: ${total_credit:,.2f}")
        print(f"   Difference:   ${balance_diff:.2f} (< $0.01)")
        print(f"   Lines exported: {len(all_lines)}")
    
    def test_individual_je_balanced(self, manager):
        """Test that each individual JE is balanced."""
        sample_jes = [
            {
                'je_id': 'JE-2024-001',
                'date': '2024-10-10',
                'lines': [
                    {'account': '6000 Supplies', 'debit': 234.56, 'credit': 0.0},
                    {'account': '1000 Checking', 'debit': 0.0, 'credit': 234.56}
                ]
            },
            {
                'je_id': 'JE-2024-002',
                'date': '2024-10-09',
                'lines': [
                    {'account': '6000 Supplies', 'debit': 100.0, 'credit': 0.0},
                    {'account': '6100 Office', 'debit': 50.0, 'credit': 0.0},
                    {'account': '1000 Checking', 'debit': 0.0, 'credit': 150.0}
                ]
            }
        ]
        
        manager.export_to_csv(sample_jes)
        all_lines = manager.get_exported_lines()
        
        # Group lines by JournalNumber
        je_groups = {}
        for line in all_lines:
            je_id = line['JournalNumber']
            if je_id not in je_groups:
                je_groups[je_id] = []
            je_groups[je_id].append(line)
        
        # Check each JE is balanced
        print(f"\n✅ Individual JE balance check:")
        for je_id, lines in je_groups.items():
            je_debit = sum(line['Debit'] for line in lines)
            je_credit = sum(line['Credit'] for line in lines)
            
            assert je_debit == je_credit, \
                f"{je_id} not balanced: Debit={je_debit}, Credit={je_credit}"
            
            print(f"   {je_id}: Debit=${je_debit:.2f}, Credit=${je_credit:.2f} ✅")
    
    def test_zero_amount_lines_allowed(self, manager):
        """Test that zero-amount lines are handled correctly."""
        sample_jes = [
            {
                'je_id': 'JE-2024-001',
                'date': '2024-10-10',
                'lines': [
                    {'account': '6000 Supplies', 'debit': 100.0, 'credit': 0.0},
                    {'account': '1000 Checking', 'debit': 0.0, 'credit': 100.0},
                    {'account': '9999 Memo Only', 'debit': 0.0, 'credit': 0.0}  # Zero line
                ]
            }
        ]
        
        result = manager.export_to_csv(sample_jes)
        all_lines = manager.get_exported_lines()
        
        # Should export all lines including zero
        assert len(all_lines) == 3, "Should export all lines including zero amounts"
        
        # Still balanced
        total_debit = sum(line['Debit'] for line in all_lines)
        total_credit = sum(line['Credit'] for line in all_lines)
        assert total_debit == total_credit
        
        print(f"\n✅ Zero-amount lines handled:")
        print(f"   Exported {len(all_lines)} lines (including 1 zero line)")
        print(f"   Still balanced: ${total_debit:.2f} = ${total_credit:.2f}")
    
    def test_large_number_precision(self, manager):
        """Test precision with large numbers."""
        sample_jes = [
            {
                'je_id': 'JE-2024-001',
                'date': '2024-10-10',
                'lines': [
                    {'account': '1000 Checking', 'debit': 123456.78, 'credit': 0.0},
                    {'account': '8000 Revenue', 'debit': 0.0, 'credit': 123456.78}
                ]
            }
        ]
        
        manager.export_to_csv(sample_jes)
        all_lines = manager.get_exported_lines()
        
        total_debit = sum(line['Debit'] for line in all_lines)
        total_credit = sum(line['Credit'] for line in all_lines)
        
        # Exact match required for large numbers
        assert total_debit == total_credit
        assert total_debit == 123456.78
        
        print(f"\n✅ Large number precision maintained:")
        print(f"   Amount: ${total_debit:,.2f}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

