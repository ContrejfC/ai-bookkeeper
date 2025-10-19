"""
Tools API - CSV Cleaner and other utilities.

Endpoints:
- POST /api/tools/csv-clean
"""
import logging
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from io import StringIO, BytesIO
import csv

router = APIRouter(prefix="/api/tools", tags=["tools"])
logger = logging.getLogger(__name__)

# Mock AI categorization - in production this would call your actual ML model
def categorize_transaction(payee: str, memo: str, amount: float) -> tuple[str, float]:
    """
    Mock categorization function. Replace with actual ML model call.
    Returns: (suggested_account, confidence)
    """
    # Simple heuristic-based categorization
    payee_lower = payee.lower() if payee else ""
    memo_lower = memo.lower() if memo else ""
    combined = f"{payee_lower} {memo_lower}"
    
    if any(word in combined for word in ["amazon", "walmart", "target", "costco"]):
        return "5000 - Cost of Goods Sold", 0.85
    elif any(word in combined for word in ["rent", "lease"]):
        return "6100 - Rent Expense", 0.90
    elif any(word in combined for word in ["utilities", "electric", "water", "gas"]):
        return "6200 - Utilities", 0.88
    elif any(word in combined for word in ["salary", "payroll", "wages"]):
        return "7000 - Payroll Expense", 0.92
    elif any(word in combined for word in ["insurance"]):
        return "6300 - Insurance", 0.85
    elif any(word in combined for word in ["bank", "fee", "charge"]):
        return "6400 - Bank Fees", 0.80
    elif any(word in combined for word in ["office", "supplies"]):
        return "6500 - Office Supplies", 0.75
    elif any(word in combined for word in ["travel", "hotel", "flight", "uber"]):
        return "6600 - Travel Expense", 0.82
    elif amount < 0:  # Expenses
        return "6000 - General Expense", 0.50
    else:  # Income
        return "4000 - Revenue", 0.60


class PreviewRow(BaseModel):
    """Single preview row"""
    date: str
    payee: str
    memo: str
    amount: float
    suggested_account: str
    confidence: float


class CSVPreviewResponse(BaseModel):
    """CSV preview response"""
    preview_rows: List[PreviewRow]
    total_rows: int
    message: str


@router.post("/csv-clean", response_model=CSVPreviewResponse)
async def csv_clean(
    file: UploadFile = File(...),
    preview: bool = Query(True, description="Preview mode (true) or full export (false)")
):
    """
    Clean and categorize CSV transactions.
    
    - **file**: CSV file with bank/card transactions
    - **preview**: If true, return first 50 rows; if false, return full cleaned CSV
    
    Preview mode: Returns JSON with up to 50 rows
    Export mode: Returns cleaned CSV stream (requires paid plan)
    """
    # Validate file
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    # Read file
    content = await file.read()
    
    # Validate size
    if len(content) > 10 * 1024 * 1024:  # 10 MB
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 10 MB")
    
    try:
        # Parse CSV
        df = pd.read_csv(BytesIO(content))
        
        # Normalize column names (common variations)
        df.columns = df.columns.str.lower().str.strip()
        
        # Map common column name variations
        column_mapping = {
            'transaction date': 'date',
            'post date': 'date',
            'description': 'payee',
            'merchant': 'payee',
            'details': 'memo',
            'note': 'memo',
            'notes': 'memo',
        }
        df.rename(columns=column_mapping, inplace=True)
        
        # Ensure required columns exist
        if 'date' not in df.columns:
            # Try to find a date column
            date_cols = [col for col in df.columns if 'date' in col.lower()]
            if date_cols:
                df.rename(columns={date_cols[0]: 'date'}, inplace=True)
            else:
                raise HTTPException(status_code=400, detail="CSV must have a date column")
        
        if 'amount' not in df.columns:
            # Try to find an amount column
            amount_cols = [col for col in df.columns if any(x in col.lower() for x in ['amount', 'value', 'total'])]
            if amount_cols:
                df.rename(columns={amount_cols[0]: 'amount'}, inplace=True)
            else:
                raise HTTPException(status_code=400, detail="CSV must have an amount column")
        
        # Ensure payee and memo columns exist (create if missing)
        if 'payee' not in df.columns:
            if 'description' in df.columns:
                df['payee'] = df['description']
            else:
                df['payee'] = ''
        
        if 'memo' not in df.columns:
            df['memo'] = ''
        
        # Clean data
        df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.strftime('%Y-%m-%d')
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0.0)
        df['payee'] = df['payee'].fillna('').astype(str)
        df['memo'] = df['memo'].fillna('').astype(str)
        
        # Remove rows with invalid dates
        df = df[df['date'].notna()]
        
        # Categorize transactions
        df[['suggested_account', 'confidence']] = df.apply(
            lambda row: pd.Series(categorize_transaction(row['payee'], row['memo'], row['amount'])),
            axis=1
        )
        
        total_rows = len(df)
        
        if preview:
            # Return preview (max 50 rows)
            preview_df = df.head(50)
            preview_rows = [
                PreviewRow(
                    date=row['date'],
                    payee=row['payee'],
                    memo=row['memo'],
                    amount=float(row['amount']),
                    suggested_account=row['suggested_account'],
                    confidence=float(row['confidence'])
                )
                for _, row in preview_df.iterrows()
            ]
            
            return CSVPreviewResponse(
                preview_rows=preview_rows,
                total_rows=total_rows,
                message=f"Preview of first {len(preview_rows)} rows (total: {total_rows})"
            )
        else:
            # Full export - would require paid plan (entitlements check)
            # For now, return CSV stream
            output = StringIO()
            df.to_csv(output, index=False)
            output.seek(0)
            
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=cleaned_{file.filename}"}
            )
            
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="CSV file is empty")
    except Exception as e:
        logger.error(f"Error processing CSV: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing CSV: {str(e)}")

