"""
Receipt Highlights API (Phase 2b).

Endpoints for receipt listing and bounding box overlays.
"""
import logging
import glob
import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.db.models import ReceiptFieldDB
from app.ocr.parser import extract_with_bboxes


router = APIRouter(prefix="/api/receipts", tags=["receipts"])
logger = logging.getLogger(__name__)


@router.get("/")
async def list_receipts(
    tenant_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List available receipts.
    
    Returns basic receipt metadata for UI listing.
    """
    # In production, query from receipts table
    # For now, list from fixtures
    
    base_path = "tests/fixtures/receipts_pdf"
    if tenant_id:
        pattern = f"{base_path}/{tenant_id}/*.pdf"
    else:
        pattern = f"{base_path}/*/*.pdf"
    
    pdf_files = glob.glob(pattern)
    
    receipts = []
    for pdf_path in pdf_files[:50]:  # Limit to 50 for performance
        parts = pdf_path.split('/')
        tenant = parts[-2]
        filename = os.path.basename(pdf_path)
        receipt_id = filename.replace('.pdf', '').replace('receipt_', '')
        
        # Try to extract basic info
        txt_path = pdf_path.replace('receipts_pdf', 'receipts').replace('.pdf', '.txt')
        vendor = "Unknown"
        date = None
        amount = None
        
        if os.path.exists(txt_path):
            try:
                fields = extract_with_bboxes(txt_path)
                vendor = fields.get('vendor', {}).get('value', 'Unknown')
                date = fields.get('date', {}).get('value')
                amount = fields.get('amount', {}).get('value') or fields.get('total', {}).get('value')
            except:
                pass
        
        receipts.append({
            "id": receipt_id,
            "tenant_id": tenant,
            "vendor": vendor,
            "date": date,
            "amount": amount,
            "filename": filename
        })
    
    return {"receipts": receipts, "count": len(receipts)}


@router.get("/{receipt_id}/fields")
async def get_receipt_fields(
    receipt_id: str,
    db: Session = Depends(get_db)
):
    """
    Get bounding boxes for receipt fields.
    
    Returns field overlays with normalized coordinates (0-1).
    """
    # Check if already in DB
    fields_db = db.query(ReceiptFieldDB).filter_by(
        receipt_id=receipt_id
    ).all()
    
    if fields_db:
        return {
            "receipt_id": receipt_id,
            "fields": [
                {
                    "name": f.field,
                    "bbox": {
                        "x": f.x,
                        "y": f.y,
                        "w": f.w,
                        "h": f.h,
                        "page": f.page
                    },
                    "confidence": f.confidence
                }
                for f in fields_db
            ]
        }
    
    # Extract from receipt text
    # Find receipt file in fixtures
    receipt_pattern = f"tests/fixtures/receipts/**/receipt_{receipt_id}.txt"
    txt_files = glob.glob(receipt_pattern, recursive=True)
    
    if not txt_files:
        # Try without receipt_ prefix
        receipt_pattern = f"tests/fixtures/receipts/**/{receipt_id}.txt"
        txt_files = glob.glob(receipt_pattern, recursive=True)
    
    if not txt_files:
        logger.warning(f"Receipt not found: {receipt_id}")
        return {"receipt_id": receipt_id, "fields": []}
    
    txt_path = txt_files[0]
    
    # Extract with bboxes
    try:
        result = extract_with_bboxes(txt_path)
    except Exception as e:
        logger.error(f"Error extracting bboxes for {receipt_id}: {e}")
        return {"receipt_id": receipt_id, "fields": [], "error": str(e)}
    
    # Store in DB for caching
    for field_name, data in result.items():
        bbox = data["bbox"]
        field_db = ReceiptFieldDB(
            receipt_id=receipt_id,
            field=field_name,
            page=bbox["page"],
            x=bbox["x"],
            y=bbox["y"],
            w=bbox["w"],
            h=bbox["h"],
            confidence=data.get("confidence", 0.85)
        )
        db.add(field_db)
    
    try:
        db.commit()
    except Exception as e:
        logger.warning(f"Could not cache bboxes for {receipt_id}: {e}")
        db.rollback()
    
    return {
        "receipt_id": receipt_id,
        "fields": [
            {
                "name": name,
                "value": str(data["value"]),
                "bbox": data["bbox"],
                "confidence": data["confidence"]
            }
            for name, data in result.items()
        ]
    }


@router.get("/{receipt_id}/pdf")
async def get_receipt_pdf(receipt_id: str):
    """
    Serve receipt PDF for viewing.
    
    In production, would stream from blob storage.
    """
    from fastapi.responses import FileResponse
    
    # Find PDF in fixtures
    pdf_pattern = f"tests/fixtures/receipts_pdf/**/receipt_{receipt_id}.pdf"
    pdf_files = glob.glob(pdf_pattern, recursive=True)
    
    if not pdf_files:
        pdf_pattern = f"tests/fixtures/receipts_pdf/**/{receipt_id}.pdf"
        pdf_files = glob.glob(pdf_pattern, recursive=True)
    
    if not pdf_files:
        raise HTTPException(status_code=404, detail="Receipt PDF not found")
    
    return FileResponse(
        pdf_files[0],
        media_type="application/pdf",
        filename=f"receipt_{receipt_id}.pdf"
    )

