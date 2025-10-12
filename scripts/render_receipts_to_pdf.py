#!/usr/bin/env python3
"""
Render PDF golden set from .txt receipts (Sprint 9 Stage B).

Generates 100 PDFs (50 per tenant) from existing .txt receipts using ReportLab.
Mirrors seeds from .txt generation for deterministic output.

Usage:
    python scripts/render_receipts_to_pdf.py

Output:
    tests/fixtures/receipts_pdf/alpha/*.pdf (50 PDFs)
    tests/fixtures/receipts_pdf/beta/*.pdf (50 PDFs)
    
Seeds:
    Alpha: 5001 (mirrored from .txt)
    Beta: 5002 (mirrored from .txt)
"""
import sys
import random
from pathlib import Path
from typing import List

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
except ImportError:
    print("❌ ReportLab not installed. Run: pip install reportlab")
    sys.exit(1)


# Configuration
ALPHA_SEED = 5001  # Mirrored from .txt generation
BETA_SEED = 5002   # Mirrored from .txt generation
PDFS_PER_TENANT = 50


def render_receipt_to_pdf(text: str, output_path: Path, seed: int):
    """
    Render a text receipt to PDF using ReportLab.
    
    Args:
        text: Receipt text content
        output_path: Path to save PDF
        seed: Random seed for any variations
    """
    rng = random.Random(seed)
    
    # Create canvas
    c = canvas.Canvas(str(output_path), pagesize=letter)
    width, height = letter
    
    # Set font
    c.setFont("Courier", 10)
    
    # Starting position
    y_position = height - 1 * inch
    line_height = 12
    
    # Split text into lines and draw
    lines = text.split('\n')
    
    for line in lines:
        # Stop if we're too close to bottom
        if y_position < 1 * inch:
            break
        
        # Draw line
        c.drawString(0.75 * inch, y_position, line[:100])  # Limit line length
        y_position -= line_height
    
    # Add a subtle border (optional)
    c.setStrokeColor(colors.lightgrey)
    c.rect(0.5 * inch, 0.5 * inch, width - 1 * inch, height - 1 * inch)
    
    # Save
    c.save()


def select_receipts_for_pdf(tenant_dir: Path, num_receipts: int, seed: int) -> List[Path]:
    """
    Select N receipts from tenant directory for PDF conversion.
    
    Uses seed for deterministic selection.
    """
    rng = random.Random(seed)
    
    all_receipts = sorted(tenant_dir.glob("*.txt"))
    
    if len(all_receipts) < num_receipts:
        print(f"⚠️  Only {len(all_receipts)} receipts available, need {num_receipts}")
        return all_receipts
    
    # Deterministic selection
    selected = rng.sample(all_receipts, num_receipts)
    
    return sorted(selected)


def render_tenant_pdfs(tenant_name: str, tenant_id: str, seed: int, num_pdfs: int):
    """
    Render PDFs for a tenant from their .txt receipts.
    """
    # Input: .txt receipts
    txt_dir = Path(__file__).parent.parent / "tests" / "fixtures" / "receipts" / tenant_id
    
    # Output: PDF receipts
    pdf_dir = Path(__file__).parent.parent / "tests" / "fixtures" / "receipts_pdf" / tenant_id
    pdf_dir.mkdir(parents=True, exist_ok=True)
    
    if not txt_dir.exists():
        print(f"❌ {txt_dir} not found. Run generate_stage_b_receipts.py first.")
        return 0
    
    # Select receipts deterministically
    selected_receipts = select_receipts_for_pdf(txt_dir, num_pdfs, seed)
    
    print(f"  Rendering {len(selected_receipts)} PDFs for {tenant_name}...")
    
    # Render each to PDF
    for idx, txt_path in enumerate(selected_receipts):
        with open(txt_path, "r") as f:
            text = f.read()
        
        # Generate PDF with deterministic naming
        pdf_filename = f"receipt_{idx+1:04d}.pdf"
        pdf_path = pdf_dir / pdf_filename
        
        # Use seed + idx for any PDF-specific variations
        render_receipt_to_pdf(text, pdf_path, seed + idx)
    
    print(f"  ✅ Wrote {len(selected_receipts)} PDFs to {pdf_dir}")
    
    return len(selected_receipts)


def main():
    """Generate PDF golden set."""
    print(f"\n{'='*80}")
    print("PDF GOLDEN SET GENERATOR (Sprint 9 Stage B)")
    print(f"{'='*80}\n")
    
    print(f"Configuration:")
    print(f"  PDFs per tenant: {PDFS_PER_TENANT}")
    print(f"  Alpha seed: {ALPHA_SEED} (mirrored from .txt)")
    print(f"  Beta seed: {BETA_SEED} (mirrored from .txt)")
    print("")
    
    # Render Alpha PDFs
    print(f"Generating Tenant Alpha PDFs (seed={ALPHA_SEED})...")
    alpha_count = render_tenant_pdfs("Alpha Manufacturing", "alpha", ALPHA_SEED, PDFS_PER_TENANT)
    
    # Render Beta PDFs
    print(f"\nGenerating Tenant Beta PDFs (seed={BETA_SEED})...")
    beta_count = render_tenant_pdfs("Beta Services", "beta", BETA_SEED, PDFS_PER_TENANT)
    
    # Summary
    total_pdfs = alpha_count + beta_count
    
    print(f"\n{'='*80}")
    print(f"✅ PDF GOLDEN SET COMPLETE")
    print(f"{'='*80}\n")
    print(f"Total PDFs: {total_pdfs}")
    print(f"  - Tenant Alpha: {alpha_count}")
    print(f"  - Tenant Beta: {beta_count}")
    print(f"\nPDFs Location: tests/fixtures/receipts_pdf/")
    print(f"  - alpha/*.pdf")
    print(f"  - beta/*.pdf")
    
    if total_pdfs >= 100:
        print(f"\n✅ Met target: ≥100 PDFs")
    else:
        print(f"\n⚠️  Below target: {total_pdfs}/100 PDFs")
    
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    main()

