#!/usr/bin/env python3
"""
Seed demo receipts for UI assessment.

Creates 6+ receipts: 3 clean, 3 messy for testing overlay functionality.
"""
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from sqlalchemy.orm import Session
from app.db.session import engine
from app.db.models import ReceiptFieldDB
import random


def seed_receipts():
    """Seed demo receipt fields with bounding boxes."""
    print("📄 Seeding demo receipt fields...")
    
    receipts_dir = Path("data/receipts")
    receipts_dir.mkdir(parents=True, exist_ok=True)
    
    with Session(engine) as db:
        # Clean receipts (high confidence, clear boxes)
        clean_receipts = [
            {
                "receipt_id": "receipt-clean-001",
                "fields": [
                    ("date", 0, 0.15, 0.12, 0.08, 0.03, 0.95),
                    ("vendor", 0, 0.15, 0.08, 0.25, 0.04, 0.96),
                    ("amount", 0, 0.15, 0.85, 0.15, 0.04, 0.94),
                    ("total", 0, 0.15, 0.92, 0.15, 0.04, 0.97),
                ]
            },
            {
                "receipt_id": "receipt-clean-002",
                "fields": [
                    ("date", 0, 0.12, 0.10, 0.10, 0.03, 0.93),
                    ("vendor", 0, 0.12, 0.06, 0.30, 0.05, 0.95),
                    ("amount", 0, 0.70, 0.88, 0.20, 0.04, 0.96),
                    ("total", 0, 0.70, 0.94, 0.20, 0.04, 0.98),
                ]
            },
            {
                "receipt_id": "receipt-clean-003",
                "fields": [
                    ("date", 0, 0.18, 0.15, 0.12, 0.03, 0.94),
                    ("vendor", 0, 0.18, 0.10, 0.22, 0.04, 0.96),
                    ("amount", 0, 0.65, 0.85, 0.18, 0.04, 0.93),
                    ("total", 0, 0.65, 0.92, 0.18, 0.04, 0.95),
                ]
            },
        ]
        
        # Messy receipts (lower confidence, irregular boxes)
        messy_receipts = [
            {
                "receipt_id": "receipt-messy-001",
                "fields": [
                    ("date", 0, 0.22, 0.18, 0.15, 0.04, 0.78),
                    ("vendor", 0, 0.25, 0.12, 0.28, 0.06, 0.72),
                    ("amount", 0, 0.58, 0.80, 0.22, 0.05, 0.81),
                    ("total", 0, 0.60, 0.90, 0.20, 0.05, 0.75),
                ]
            },
            {
                "receipt_id": "receipt-messy-002",
                "fields": [
                    ("date", 0, 0.10, 0.20, 0.18, 0.05, 0.68),
                    ("vendor", 0, 0.12, 0.15, 0.32, 0.07, 0.70),
                    ("amount", 0, 0.55, 0.82, 0.25, 0.06, 0.74),
                    ("total", 0, 0.58, 0.93, 0.23, 0.06, 0.69),
                ]
            },
            {
                "receipt_id": "receipt-messy-003",
                "fields": [
                    ("date", 0, 0.08, 0.22, 0.20, 0.06, 0.65),
                    ("vendor", 0, 0.10, 0.18, 0.35, 0.08, 0.67),
                    ("amount", 0, 0.50, 0.78, 0.28, 0.07, 0.71),
                    ("total", 0, 0.52, 0.88, 0.26, 0.07, 0.66),
                ]
            },
        ]
        
        all_receipts = clean_receipts + messy_receipts
        
        for receipt in all_receipts:
            receipt_id = receipt["receipt_id"]
            
            # Create dummy receipt file
            receipt_file = receipts_dir / f"{receipt_id}.pdf"
            if not receipt_file.exists():
                receipt_file.write_text(f"Demo receipt: {receipt_id}\n")
            
            # Add fields to database
            for field_name, page, x, y, w, h, confidence in receipt["fields"]:
                existing = db.query(ReceiptFieldDB).filter_by(
                    receipt_id=receipt_id,
                    field=field_name
                ).first()
                
                if not existing:
                    field = ReceiptFieldDB(
                        receipt_id=receipt_id,
                        field=field_name,
                        page=page,
                        x=x,
                        y=y,
                        w=w,
                        h=h,
                        confidence=confidence
                    )
                    db.add(field)
        
        db.commit()
        print(f"✅ Seeded {len(all_receipts)} receipts with bounding boxes")
        print(f"   • {len(clean_receipts)} clean receipts (>90% confidence)")
        print(f"   • {len(messy_receipts)} messy receipts (65-80% confidence)")
        print(f"\n📁 Receipt files: {receipts_dir}")


if __name__ == "__main__":
    seed_receipts()

