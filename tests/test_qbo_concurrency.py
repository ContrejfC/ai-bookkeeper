#!/usr/bin/env python3
"""
Unit tests for QBO export concurrency safety (Sprint 9 Stage F).

Tests that concurrent exports don't create duplicate lines.
"""
import pytest
import threading
import time
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.test_qbo_idempotency import QBOExportManager


class ConcurrentQBOExportManager(QBOExportManager):
    """Thread-safe QBO export manager."""
    
    def __init__(self):
        super().__init__()
        self._lock = threading.Lock()
    
    def export_to_csv(self, journal_entries: list) -> dict:
        """
        Thread-safe export using lock for UPSERT simulation.
        
        Simulates ON CONFLICT DO NOTHING behavior in PostgreSQL.
        """
        with self._lock:
            # Simulate database UPSERT with conflict resolution
            return super().export_to_csv(journal_entries)


class TestQBOConcurrency:
    """Test QBO export concurrency safety."""
    
    @pytest.fixture
    def manager(self):
        """Create a thread-safe export manager."""
        return ConcurrentQBOExportManager()
    
    @pytest.fixture
    def sample_je(self):
        """Sample journal entry for testing."""
        return {
            'je_id': 'JE-2024-001',
            'date': '2024-10-10',
            'memo': 'Office supplies',
            'lines': [
                {'account': '6000 Supplies', 'debit': 234.56, 'credit': 0.0},
                {'account': '1000 Checking', 'debit': 0.0, 'credit': 234.56}
            ]
        }
    
    def test_race_no_duplicates(self, manager, sample_je):
        """
        CRITICAL TEST: Concurrent exports don't create duplicates.
        
        Simulates race condition where multiple workers try to export
        the same JE simultaneously. Only one should succeed.
        """
        results = []
        errors = []
        
        def export_worker(worker_id: int):
            """Worker thread that attempts export."""
            try:
                result = manager.export_to_csv([sample_je])
                results.append({
                    'worker_id': worker_id,
                    'new': result['new'],
                    'skipped': result['skipped']
                })
            except Exception as e:
                errors.append({'worker_id': worker_id, 'error': str(e)})
        
        # Launch 10 concurrent workers
        threads = []
        num_workers = 10
        
        for i in range(num_workers):
            thread = threading.Thread(target=export_worker, args=(i,))
            threads.append(thread)
        
        # Start all threads nearly simultaneously
        for thread in threads:
            thread.start()
        
        # Wait for all to complete
        for thread in threads:
            thread.join()
        
        # Assertions
        assert len(errors) == 0, f"No worker should error: {errors}"
        assert len(results) == num_workers, f"All workers should complete"
        
        # Count how many succeeded vs skipped
        new_count = sum(r['new'] for r in results)
        skipped_count = sum(r['skipped'] for r in results)
        
        # CRITICAL: Only 1 should export, rest should skip
        assert new_count == 1, \
            f"Only 1 worker should export (got {new_count})"
        assert skipped_count == num_workers - 1, \
            f"All other workers should skip (got {skipped_count})"
        
        # Verify no duplicate lines
        all_lines = manager.get_exported_lines()
        assert len(all_lines) == 2, \
            f"Should have exactly 2 lines (got {len(all_lines)})"
        
        print(f"\n✅ Concurrency test passed:")
        print(f"   Workers: {num_workers}")
        print(f"   New exports: {new_count} (expected 1)")
        print(f"   Skipped: {skipped_count} (expected {num_workers - 1})")
        print(f"   Total lines: {len(all_lines)} (no duplicates)")
    
    def test_concurrent_different_jes(self, manager):
        """Test concurrent export of different JEs."""
        jes = [
            {
                'je_id': f'JE-2024-{i:03d}',
                'date': '2024-10-10',
                'lines': [
                    {'account': '6000 Supplies', 'debit': 100.0 + i, 'credit': 0.0},
                    {'account': '1000 Checking', 'debit': 0.0, 'credit': 100.0 + i}
                ]
            }
            for i in range(5)
        ]
        
        results = []
        
        def export_worker(je):
            """Export a single JE."""
            result = manager.export_to_csv([je])
            results.append(result)
        
        # Launch concurrent workers for different JEs
        threads = [threading.Thread(target=export_worker, args=(je,)) for je in jes]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All should succeed (different ExternalIds)
        total_new = sum(r['new'] for r in results)
        total_skipped = sum(r['skipped'] for r in results)
        
        assert total_new == 5, "All 5 JEs should export"
        assert total_skipped == 0, "No skips for different JEs"
        
        all_lines = manager.get_exported_lines()
        assert len(all_lines) == 10, "Should have 10 lines (5 JEs × 2 lines)"
        
        print(f"\n✅ Concurrent different JEs:")
        print(f"   JEs exported: {total_new}")
        print(f"   Total lines: {len(all_lines)}")
    
    def test_interleaved_exports(self, manager, sample_je):
        """Test interleaved export attempts with small delays."""
        results = []
        
        def delayed_export(delay_ms: int):
            """Export with a small delay."""
            time.sleep(delay_ms / 1000.0)
            result = manager.export_to_csv([sample_je])
            results.append(result)
        
        # Launch workers with staggered delays (0ms, 5ms, 10ms, 15ms, 20ms)
        threads = [
            threading.Thread(target=delayed_export, args=(i * 5,))
            for i in range(5)
        ]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # First should succeed, rest skip
        new_count = sum(r['new'] for r in results)
        skipped_count = sum(r['skipped'] for r in results)
        
        assert new_count == 1, "Only first should export"
        assert skipped_count == 4, "Rest should skip"
        
        all_lines = manager.get_exported_lines()
        assert len(all_lines) == 2, "Should have exactly 2 lines"
        
        print(f"\n✅ Interleaved exports:")
        print(f"   New: {new_count}, Skipped: {skipped_count}")
        print(f"   No duplicates from timing variations")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

