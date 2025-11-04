#!/usr/bin/env python3
"""
Quick script to analyze sample bank statements and identify banks.
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import pdfplumber
except ImportError:
    print("ERROR: pdfplumber not installed. Run: pip install pdfplumber")
    sys.exit(1)

def analyze_pdf(pdf_path):
    """Analyze a PDF and print key information."""
    print(f"\n{'='*80}")
    print(f"Analyzing: {pdf_path.name}")
    print(f"{'='*80}")
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"Pages: {len(pdf.pages)}")
            
            if len(pdf.pages) > 0:
                first_page = pdf.pages[0]
                text = first_page.extract_text() or ""
                
                # Print first 1000 characters
                print(f"\nFirst 1000 characters:")
                print(text[:1000])
                
                # Look for bank names
                bank_keywords = [
                    'chase', 'jpmorgan', 'wells fargo', 'bank of america', 
                    'citibank', 'citi', 'goldman sachs', 'pnc', 'morgan stanley',
                    'u.s. bank', 'usbank', 'truist', 'first citizens', 'bmo',
                    'td bank', 'capital one', 'schwab', 'charles schwab',
                    'm&t bank', 'fifth third', 'huntington', 'keybank', 'keycorp',
                    'citizens bank', 'american express', 'amex'
                ]
                
                text_lower = text.lower()
                found_banks = [kw for kw in bank_keywords if kw in text_lower]
                
                if found_banks:
                    print(f"\n🏦 Detected Banks: {', '.join(found_banks)}")
                
                # Look for statement keywords
                if 'statement' in text_lower:
                    print("✅ Contains 'statement'")
                if 'account' in text_lower:
                    print("✅ Contains 'account'")
                if 'balance' in text_lower:
                    print("✅ Contains 'balance'")
                
                # Try to extract tables
                tables = first_page.extract_tables()
                if tables:
                    print(f"\n📊 Found {len(tables)} table(s)")
                    for i, table in enumerate(tables[:2]):  # First 2 tables only
                        if table and len(table) > 0:
                            print(f"\nTable {i+1} headers: {table[0]}")
    
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    samples_dir = Path(__file__).parent.parent / "Sample Bankstatements"
    
    if not samples_dir.exists():
        print(f"ERROR: {samples_dir} not found")
        sys.exit(1)
    
    pdf_files = list(samples_dir.glob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {samples_dir}")
        sys.exit(1)
    
    print(f"Found {len(pdf_files)} PDF files")
    
    for pdf_file in sorted(pdf_files):
        analyze_pdf(pdf_file)
    
    print(f"\n{'='*80}")
    print("Analysis complete!")
    print(f"{'='*80}")

if __name__ == '__main__':
    main()



