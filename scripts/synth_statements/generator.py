"""
Synthetic Statement PDF Generator
=================================

Generates bank statement PDFs from YAML style definitions.

Usage:
    from scripts.synth_statements import generate_statement
    
    generate_statement(
        style_path="scripts/synth_statements/styles/checking.yaml",
        output_path="statement.pdf",
        num_rows=50,
        num_pages=3
    )
"""

import random
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import List, Dict, Any, Optional
import yaml

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.pdfgen import canvas
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False
    print("Warning: ReportLab not installed. Install with: pip install reportlab")


class StatementGenerator:
    """Generate synthetic bank statement PDFs."""
    
    def __init__(self, style_config: Dict[str, Any]):
        """
        Initialize generator with style configuration.
        
        Args:
            style_config: Loaded YAML style configuration
        """
        if not HAS_REPORTLAB:
            raise ImportError("ReportLab is required. Install with: pip install reportlab")
        
        self.config = style_config
        self.name = style_config.get('name', 'statement')
        self.header_config = style_config.get('header', {})
        self.table_config = style_config.get('table', {})
        self.layout_config = style_config.get('layout', {})
        self.noise_config = style_config.get('noise', {})
    
    def generate(self, output_path: Path, num_rows: int = 50, num_pages: int = 1,
                 account_number: str = "****1234", start_balance: float = 10000.00,
                 add_noise: bool = False):
        """
        Generate a statement PDF.
        
        Args:
            output_path: Where to save the PDF
            num_rows: Number of transaction rows
            num_pages: Number of pages
            account_number: Account number (masked)
            start_balance: Starting balance
            add_noise: Whether to add noise/rotation
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate transactions
        transactions = self._generate_transactions(num_rows, start_balance)
        
        # Create PDF
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        # Build story (content)
        story = []
        
        # Add header
        story.extend(self._create_header(account_number, transactions))
        story.append(Spacer(1, 0.25*inch))
        
        # Add transaction table
        rows_per_page = num_rows // num_pages if num_pages > 1 else num_rows
        
        for page_num in range(num_pages):
            start_idx = page_num * rows_per_page
            end_idx = min(start_idx + rows_per_page, num_rows)
            page_txns = transactions[start_idx:end_idx]
            
            table = self._create_transaction_table(page_txns)
            story.append(table)
            
            if page_num < num_pages - 1:
                story.append(Spacer(1, 0.5*inch))
        
        # Build PDF
        doc.build(story)
        
        # Apply noise if requested
        if add_noise:
            self._apply_noise(output_path)
    
    def _generate_transactions(self, num_rows: int, start_balance: float) -> List[Dict[str, Any]]:
        """Generate synthetic transaction data."""
        transactions = []
        running_balance = Decimal(str(start_balance))
        
        # Start date
        current_date = datetime.now() - timedelta(days=30)
        
        # Transaction templates
        debit_templates = [
            "Office Supplies Purchase",
            "Utility Bill Payment",
            "Payroll Processing",
            "Equipment Purchase",
            "Software Subscription",
            "Insurance Payment",
            "Rent Payment",
            "Professional Services",
            "Travel Expenses",
            "Marketing Costs"
        ]
        
        credit_templates = [
            "Client Payment - Invoice #{inv}",
            "Customer Deposit",
            "Refund Received",
            "Interest Income",
            "Wire Transfer Received",
            "ACH Credit",
            "Deposit"
        ]
        
        for i in range(num_rows):
            # Random debit or credit (60% debit, 40% credit)
            is_debit = random.random() < 0.6
            
            if is_debit:
                amount = -round(random.uniform(10, 2000), 2)
                description = random.choice(debit_templates)
            else:
                amount = round(random.uniform(100, 5000), 2)
                description = random.choice(credit_templates).format(inv=random.randint(1000, 9999))
            
            running_balance += Decimal(str(amount))
            
            transactions.append({
                'date': current_date.strftime('%m/%d/%Y'),
                'description': description,
                'amount': amount,
                'balance': float(running_balance)
            })
            
            # Advance date by 0-2 days
            current_date += timedelta(days=random.randint(0, 2))
        
        return transactions
    
    def _create_header(self, account_number: str, transactions: List[Dict]) -> List:
        """Create statement header."""
        styles = getSampleStyleSheet()
        header_style = ParagraphStyle(
            'HeaderStyle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=12
        )
        
        info_style = ParagraphStyle(
            'InfoStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#333333')
        )
        
        elements = []
        
        # Bank name
        bank_name = self.header_config.get('tokens', [])[0] if self.header_config.get('tokens') else "Bank Statement"
        elements.append(Paragraph(f"<b>{bank_name}</b>", header_style))
        
        # Account info
        start_date = transactions[0]['date'] if transactions else 'N/A'
        end_date = transactions[-1]['date'] if transactions else 'N/A'
        
        info_lines = [
            f"<b>Account Number:</b> {account_number}",
            f"<b>Statement Period:</b> {start_date} to {end_date}",
            f"<b>Beginning Balance:</b> ${transactions[0]['balance'] - transactions[0]['amount']:.2f}" if transactions else "",
            f"<b>Ending Balance:</b> ${transactions[-1]['balance']:.2f}" if transactions else ""
        ]
        
        for line in info_lines:
            if line:
                elements.append(Paragraph(line, info_style))
        
        return elements
    
    def _create_transaction_table(self, transactions: List[Dict]) -> Table:
        """Create transaction table."""
        # Get table headers from config
        headers = self.table_config.get('headers', ['Date', 'Description', 'Amount', 'Balance'])
        
        # Create table data
        data = [headers]
        
        for txn in transactions:
            row = []
            for header in headers:
                if header.lower() == 'date':
                    row.append(txn['date'])
                elif header.lower() == 'description':
                    row.append(txn['description'][:40])  # Truncate long descriptions
                elif header.lower() == 'amount':
                    amount = txn['amount']
                    if amount < 0:
                        row.append(f"${abs(amount):.2f}")
                    else:
                        row.append(f"${amount:.2f}")
                elif header.lower() == 'balance':
                    row.append(f"${txn['balance']:.2f}")
                else:
                    row.append("")
            data.append(row)
        
        # Create table
        table = Table(data, colWidths=[1*inch, 3.5*inch, 1*inch, 1.25*inch])
        
        # Style the table
        table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a90e2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            
            # Data rows
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),   # Date
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),   # Description
            ('ALIGN', (2, 1), (2, -1), 'RIGHT'),  # Amount
            ('ALIGN', (3, 1), (3, -1), 'RIGHT'),  # Balance
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#4a90e2')),
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')])
        ]))
        
        return table
    
    def _apply_noise(self, pdf_path: Path):
        """Apply noise/rotation to simulate scans (placeholder)."""
        # In a full implementation, this would:
        # 1. Load the PDF
        # 2. Rotate slightly (±1 degree)
        # 3. Add speckle noise
        # 4. Reduce DPI
        # This requires additional libraries like PIL/Pillow
        pass


def generate_statement(style_path: Path, output_path: Path, num_rows: int = 50,
                       num_pages: int = 1, account_number: str = "****1234",
                       start_balance: float = 10000.00, add_noise: bool = False):
    """
    Convenience function to generate a statement.
    
    Args:
        style_path: Path to YAML style definition
        output_path: Where to save the PDF
        num_rows: Number of transaction rows
        num_pages: Number of pages
        account_number: Account number (masked)
        start_balance: Starting balance
        add_noise: Whether to add noise/rotation
    """
    # Load style
    with open(style_path, 'r') as f:
        style_config = yaml.safe_load(f)
    
    # Generate
    generator = StatementGenerator(style_config)
    generator.generate(output_path, num_rows, num_pages, account_number, start_balance, add_noise)
    
    print(f"✅ Generated statement: {output_path}")
    print(f"   Rows: {num_rows}, Pages: {num_pages}")


# CLI interface
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate synthetic bank statement PDFs')
    parser.add_argument('--style', type=Path, required=True, help='Path to style YAML')
    parser.add_argument('--output', type=Path, required=True, help='Output PDF path')
    parser.add_argument('--rows', type=int, default=50, help='Number of transactions')
    parser.add_argument('--pages', type=int, default=1, help='Number of pages')
    parser.add_argument('--account', type=str, default='****1234', help='Account number')
    parser.add_argument('--balance', type=float, default=10000.00, help='Starting balance')
    parser.add_argument('--noise', action='store_true', help='Add noise/rotation')
    
    args = parser.parse_args()
    
    generate_statement(
        style_path=args.style,
        output_path=args.output,
        num_rows=args.rows,
        num_pages=args.pages,
        account_number=args.account,
        start_balance=args.balance,
        add_noise=args.noise
    )



