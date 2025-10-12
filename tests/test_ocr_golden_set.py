#!/usr/bin/env python3
"""
OCR Golden Set Accuracy Test (Sprint 9 Stage B).

Tests OCR parser on 100 PDF golden set and validates ≥90% field-level accuracy.
Exports results to artifacts/ocr_golden_results.json.

Fields tested:
- date: Receipt date
- amount: First amount (often subtotal)
- vendor: Vendor/counterparty name
- total: Total amount (with "Total" keyword)

Minimum required: date, amount, vendor
"""
import pytest
import json
import re
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Add parent to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ocr.parser import OCRParser


FIXTURES_DIR = Path(__file__).parent / "fixtures"
PDFS_DIR = FIXTURES_DIR / "receipts_pdf"
TXT_DIR = FIXTURES_DIR / "receipts"
ARTIFACTS_DIR = Path(__file__).parent.parent / "artifacts"
TARGET_ACCURACY = 0.90


class TestOCRGoldenSet:
    """Test OCR parser on golden set PDFs."""
    
    @pytest.fixture
    def ocr_parser(self):
        """Initialize OCR parser."""
        return OCRParser(accuracy_target=0.90)
    
    @pytest.fixture
    def pdf_files(self):
        """Get all PDF files from golden set."""
        alpha_pdfs = list((PDFS_DIR / "alpha").glob("*.pdf"))
        beta_pdfs = list((PDFS_DIR / "beta").glob("*.pdf"))
        return sorted(alpha_pdfs + beta_pdfs)
    
    def _extract_ground_truth(self, txt_path: Path) -> Dict[str, Any]:
        """
        Extract ground truth fields from .txt file.
        
        This is our "clean" reference before OCR noise.
        """
        with open(txt_path, "r") as f:
            text = f.read()
        
        # Date
        date_match = re.search(r'Date[:\s]+(\d{1,2}/\d{1,2}/\d{4})', text, re.IGNORECASE)
        date_value = date_match.group(1) if date_match else None
        
        # Amount (first occurrence)
        amount_match = re.search(r'\$\s*(\d+[.,]\d{2})', text)
        amount_value = float(amount_match.group(1).replace(',', '')) if amount_match else None
        
        # Total
        total_match = re.search(r'Total[:\s]+\$\s*(\d+[.,]\d{2})', text, re.IGNORECASE)
        total_value = float(total_match.group(1).replace(',', '')) if total_match else None
        
        # Vendor
        vendor_match = re.search(r'(?:From|INVOICE)[\s:]+([A-Za-z][A-Za-z\s&]+?)(?:\n|$|\s{2,})', text, re.IGNORECASE | re.MULTILINE)
        if not vendor_match:
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            vendor_value = lines[0] if lines else None
        else:
            vendor_value = vendor_match.group(1).strip()
        
        return {
            "date": date_value,
            "amount": amount_value,
            "vendor": vendor_value,
            "total": total_value
        }
    
    def _get_txt_path(self, pdf_path: Path) -> Path:
        """Get corresponding .txt path for a PDF."""
        parts = pdf_path.parts
        tenant = parts[-2]
        filename = pdf_path.stem + ".txt"
        return TXT_DIR / tenant / filename
    
    def _compare_fields(self, ground_truth: Dict[str, Any], extracted: Dict[str, Any]) -> Dict[str, bool]:
        """
        Compare extracted fields with ground truth.
        
        Returns:
            Dictionary of {field: is_correct}
        """
        results = {}
        
        # Date comparison
        if ground_truth.get("date") and extracted.get("date"):
            results["date"] = ground_truth["date"] == extracted["date"]
        elif not ground_truth.get("date") and not extracted.get("date"):
            results["date"] = True  # Both missing
        else:
            results["date"] = False
        
        # Amount comparison (within 1% tolerance for OCR rounding)
        if ground_truth.get("amount") and extracted.get("amount"):
            diff = abs(ground_truth["amount"] - extracted["amount"])
            tolerance = ground_truth["amount"] * 0.01
            results["amount"] = diff <= tolerance
        elif not ground_truth.get("amount") and not extracted.get("amount"):
            results["amount"] = True
        else:
            results["amount"] = False
        
        # Vendor comparison (exact match or first 5 chars match for OCR typos)
        if ground_truth.get("vendor") and extracted.get("vendor"):
            gt_vendor = ground_truth["vendor"].lower().strip()
            ex_vendor = extracted["vendor"].lower().strip()
            results["vendor"] = (gt_vendor == ex_vendor) or (gt_vendor[:5] == ex_vendor[:5])
        elif not ground_truth.get("vendor") and not extracted.get("vendor"):
            results["vendor"] = True
        else:
            results["vendor"] = False
        
        # Total comparison
        if ground_truth.get("total") and extracted.get("total"):
            diff = abs(ground_truth["total"] - extracted["total"])
            tolerance = ground_truth["total"] * 0.01
            results["total"] = diff <= tolerance
        elif not ground_truth.get("total") and not extracted.get("total"):
            results["total"] = True
        else:
            results["total"] = False
        
        return results
    
    def test_ocr_accuracy_on_golden_set(self, ocr_parser, pdf_files):
        """
        Test OCR accuracy on entire golden set.
        
        Validates ≥90% accuracy for date, amount, vendor fields.
        """
        results = []
        field_stats = {
            "date": {"correct": 0, "total": 0},
            "amount": {"correct": 0, "total": 0},
            "vendor": {"correct": 0, "total": 0},
            "total": {"correct": 0, "total": 0}
        }
        
        for pdf_path in pdf_files:
            txt_path = self._get_txt_path(pdf_path)
            
            if not txt_path.exists():
                continue
            
            # Get ground truth
            ground_truth = self._extract_ground_truth(txt_path)
            
            # Parse PDF with OCR
            # Use deterministic seed based on filename for reproducibility
            seed = int(pdf_path.stem.split('_')[-1])
            extracted = ocr_parser.parse_pdf(pdf_path, seed=seed)
            
            # Compare
            comparison = self._compare_fields(ground_truth, extracted)
            
            # Update stats
            for field, is_correct in comparison.items():
                field_stats[field]["total"] += 1
                if is_correct:
                    field_stats[field]["correct"] += 1
            
            # Store result
            results.append({
                "pdf": str(pdf_path.name),
                "tenant": pdf_path.parts[-2],
                "ground_truth": ground_truth,
                "extracted": {
                    "date": extracted.get("date"),
                    "amount": extracted.get("amount"),
                    "vendor": extracted.get("vendor"),
                    "total": extracted.get("total")
                },
                "comparison": comparison,
                "ocr_confidence": extracted.get("confidence", 0.0)
            })
        
        # Calculate per-field accuracies
        accuracies = {}
        for field, stats in field_stats.items():
            if stats["total"] > 0:
                accuracies[field] = stats["correct"] / stats["total"]
            else:
                accuracies[field] = 0.0
        
        # Calculate overall accuracy (minimum required fields: date, amount, vendor)
        required_fields = ["date", "amount", "vendor"]
        overall_correct = sum(field_stats[f]["correct"] for f in required_fields)
        overall_total = sum(field_stats[f]["total"] for f in required_fields)
        overall_accuracy = overall_correct / overall_total if overall_total > 0 else 0.0
        
        # Export to JSON
        ARTIFACTS_DIR.mkdir(exist_ok=True)
        output_path = ARTIFACTS_DIR / "ocr_golden_results.json"
        
        export_data = {
            "test_date": datetime.now().isoformat(),
            "total_pdfs": len(results),
            "target_accuracy": TARGET_ACCURACY,
            "overall_accuracy": overall_accuracy,
            "per_field_accuracy": accuracies,
            "field_stats": field_stats,
            "results": results[:10]  # Include first 10 for reference
        }
        
        with open(output_path, "w") as f:
            json.dump(export_data, f, indent=2)
        
        # Print summary
        print(f"\n{'='*80}")
        print(f"OCR GOLDEN SET RESULTS")
        print(f"{'='*80}\n")
        print(f"Total PDFs tested: {len(results)}")
        print(f"Target accuracy: {TARGET_ACCURACY:.1%}")
        print(f"\nPer-field accuracy:")
        for field, accuracy in accuracies.items():
            status = "✅" if accuracy >= TARGET_ACCURACY else "⚠️ "
            print(f"  {field:10s}: {accuracy:.2%} {status}")
        print(f"\nOverall accuracy (date+amount+vendor): {overall_accuracy:.2%}")
        print(f"Results exported to: {output_path}")
        print(f"{'='*80}\n")
        
        # Assert minimum required fields meet target
        assert accuracies["date"] >= TARGET_ACCURACY, \
            f"Date accuracy {accuracies['date']:.2%} < {TARGET_ACCURACY:.1%}"
        assert accuracies["amount"] >= TARGET_ACCURACY, \
            f"Amount accuracy {accuracies['amount']:.2%} < {TARGET_ACCURACY:.1%}"
        assert accuracies["vendor"] >= TARGET_ACCURACY, \
            f"Vendor accuracy {accuracies['vendor']:.2%} < {TARGET_ACCURACY:.1%}"
    
    def test_pdf_count_meets_target(self, pdf_files):
        """Verify we have ≥100 PDFs in golden set."""
        assert len(pdf_files) >= 100, f"Expected ≥100 PDFs, found {len(pdf_files)}"
    
    def test_pdfs_readable(self, pdf_files):
        """Verify PDFs are valid files."""
        for pdf_path in pdf_files[:10]:  # Sample first 10
            assert pdf_path.exists(), f"PDF not found: {pdf_path}"
            assert pdf_path.stat().st_size > 0, f"PDF is empty: {pdf_path}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

