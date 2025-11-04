#!/usr/bin/env python3
"""
Synthetic Bank Statement Generator
===================================

Generate synthetic bank statement PDFs for testing template matchers.

NO REAL LOGOS OR TRADEMARKS. Text-only lookalikes.

Usage:
    python scripts/generate_synthetic_statement.py --style chase --out /tmp/statement.pdf
    python scripts/generate_synthetic_statement.py --style wells_fargo --account "****1234" --out test.pdf
"""

import argparse
import sys
from pathlib import Path
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Dict, Optional
import random

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False
    print("ERROR: reportlab not installed. Install with: pip install reportlab")
    sys.exit(1)

from app.ingestion.templates.registry import TemplateRegistry


class SyntheticStatementGenerator:
    """Generate synthetic bank statement PDFs."""
    
    def __init__(self, style: str, template_registry: Optional[TemplateRegistry] = None):
        """
        Initialize generator.
        
        Args:
            style: Template style name (e.g., "chase", "wells_fargo")
            template_registry: Optional registry (will create default if not provided)
        """
        self.style = style
        
        if template_registry is None:
            template_registry = TemplateRegistry()
        
        self.template = template_registry.get_template_by_name(f"{style}_checking_v1")
        
        if not self.template:
            raise ValueError(f"Template not found for style: {style}")
        
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='StatementTitle',
            parent=self.styles['Title'],
            fontSize=16,
            textColor=colors.black,
            spaceAfter=12,
            alignment=TA_CENTER
        ))
        
        # Header style
        self.styles.add(ParagraphStyle(
            name='StatementHeader',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            spaceAfter=6
        ))
        
        # Small text style
        self.styles.add(ParagraphStyle(
            name='SmallText',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.gray
        ))
    
    def generate(
        self,
        output_path: str,
        account_number: str = "****1234",
        statement_period: Optional[tuple] = None,
        beginning_balance: Decimal = Decimal("1000.00"),
        transaction_count: int = 20
    ):
        """
        Generate a synthetic statement PDF.
        
        Args:
            output_path: Path to save PDF
            account_number: Masked account number
            statement_period: Tuple of (start_date, end_date) or None for last month
            beginning_balance: Starting balance
            transaction_count: Number of transactions to generate
        """
        # Set up document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )
        
        # Build content
        story = []
        
        # Add header
        story.extend(self._build_header(account_number, statement_period, beginning_balance))
        
        # Add transactions table
        transactions = self._generate_transactions(
            beginning_balance,
            transaction_count,
            statement_period
        )
        
        story.extend(self._build_transaction_table(transactions, beginning_balance))
        
        # Add footer
        story.extend(self._build_footer())
        
        # Build PDF
        doc.build(story)
        print(f"Generated synthetic statement: {output_path}")
    
    def _build_header(
        self,
        account_number: str,
        statement_period: Optional[tuple],
        beginning_balance: Decimal
    ) -> List:
        """Build header section."""
        elements = []
        
        # Title
        bank_name = self.template.bank_name or "Bank"
        elements.append(Paragraph(f"{bank_name} Statement", self.styles['StatementTitle']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Statement info
        if statement_period is None:
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
        else:
            start_date, end_date = statement_period
        
        info_text = f"""
        <b>Statement Period:</b> {start_date.strftime('%m/%d/%Y')} - {end_date.strftime('%m/%d/%Y')}<br/>
        <b>Account Number:</b> {account_number}<br/>
        <b>Beginning Balance:</b> ${beginning_balance:,.2f}<br/>
        """
        
        elements.append(Paragraph(info_text, self.styles['StatementHeader']))
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _generate_transactions(
        self,
        beginning_balance: Decimal,
        count: int,
        statement_period: Optional[tuple]
    ) -> List[Dict]:
        """Generate synthetic transactions."""
        if statement_period is None:
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
        else:
            start_date, end_date = statement_period
        
        # Generate random dates within period
        days_in_period = (end_date - start_date).days
        
        transactions = []
        running_balance = beginning_balance
        
        # Common transaction descriptions
        merchants = [
            "GROCERY STORE", "GAS STATION", "RESTAURANT", "PHARMACY",
            "ONLINE PURCHASE", "UTILITY PAYMENT", "PAYROLL DEPOSIT",
            "ATM WITHDRAWAL", "CHECK #1234", "TRANSFER", "SUBSCRIPTION SERVICE",
            "COFFEE SHOP", "BOOKSTORE", "DEPARTMENT STORE", "ELECTRONICS STORE"
        ]
        
        for i in range(count):
            # Random date
            day_offset = random.randint(0, days_in_period)
            txn_date = start_date + timedelta(days=day_offset)
            
            # Random transaction
            is_debit = random.random() < 0.7  # 70% debits, 30% credits
            amount = Decimal(str(round(random.uniform(5.0, 500.0), 2)))
            
            if is_debit:
                amount = -amount
                description = random.choice(merchants[:11])  # First 11 are debits
            else:
                description = random.choice(merchants[11:])  # Last few are credits
            
            running_balance += amount
            
            transactions.append({
                'date': txn_date,
                'description': description,
                'amount': amount,
                'balance': running_balance
            })
        
        # Sort by date
        transactions.sort(key=lambda x: x['date'])
        
        # Recompute balances in chronological order
        running_balance = beginning_balance
        for txn in transactions:
            running_balance += txn['amount']
            txn['balance'] = running_balance
        
        return transactions
    
    def _build_transaction_table(self, transactions: List[Dict], beginning_balance: Decimal) -> List:
        """Build transactions table."""
        elements = []
        
        # Determine table headers based on template style
        # Check if template uses separate debit/credit columns
        template_headers = self.template.match.table_headers
        
        # Default to single amount column
        use_separate_columns = any(
            'debit' in str(h).lower() or 'credit' in str(h).lower()
            for h in template_headers
        )
        
        if use_separate_columns:
            # Separate debit/credit columns
            headers = ['Date', 'Description', 'Debits', 'Credits', 'Balance']
            
            data = [headers]
            for txn in transactions:
                debit = f"${abs(txn['amount']):,.2f}" if txn['amount'] < 0 else ""
                credit = f"${txn['amount']:,.2f}" if txn['amount'] >= 0 else ""
                
                row = [
                    txn['date'].strftime('%m/%d/%Y'),
                    txn['description'],
                    debit,
                    credit,
                    f"${txn['balance']:,.2f}"
                ]
                data.append(row)
            
            col_widths = [1.0*inch, 2.5*inch, 1.0*inch, 1.0*inch, 1.2*inch]
        
        else:
            # Single amount column
            headers = ['Date', 'Description', 'Amount', 'Balance']
            
            data = [headers]
            for txn in transactions:
                amount_str = f"${abs(txn['amount']):,.2f}"
                if txn['amount'] < 0:
                    amount_str = f"-{amount_str}"
                
                row = [
                    txn['date'].strftime('%m/%d/%Y'),
                    txn['description'],
                    amount_str,
                    f"${txn['balance']:,.2f}"
                ]
                data.append(row)
            
            col_widths = [1.0*inch, 3.0*inch, 1.2*inch, 1.2*inch]
        
        # Create table
        table = Table(data, colWidths=col_widths)
        
        # Style table
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),  # Date
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),  # Description
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),  # Amounts
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Add summary
        ending_balance = transactions[-1]['balance'] if transactions else beginning_balance
        
        summary_text = f"<b>Ending Balance:</b> ${ending_balance:,.2f}"
        elements.append(Paragraph(summary_text, self.styles['StatementHeader']))
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _build_footer(self) -> List:
        """Build footer section."""
        elements = []
        
        footer_text = """
        <b>Questions? Call</b> 1-800-555-0100<br/>
        <br/>
        This is a synthetic statement for testing purposes only.<br/>
        Not a real bank document. Member FDIC.
        """
        
        elements.append(Paragraph(footer_text, self.styles['SmallText']))
        
        return elements


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate synthetic bank statement PDFs for testing'
    )
    parser.add_argument(
        '--style',
        required=True,
        choices=['chase', 'wells_fargo', 'fifth_third', 'bank_of_america', 'us_bank'],
        help='Bank statement style'
    )
    parser.add_argument(
        '--out',
        required=True,
        help='Output PDF path'
    )
    parser.add_argument(
        '--account',
        default='****1234',
        help='Masked account number'
    )
    parser.add_argument(
        '--transactions',
        type=int,
        default=20,
        help='Number of transactions to generate'
    )
    parser.add_argument(
        '--balance',
        type=float,
        default=1000.0,
        help='Beginning balance'
    )
    
    args = parser.parse_args()
    
    try:
        generator = SyntheticStatementGenerator(args.style)
        generator.generate(
            output_path=args.out,
            account_number=args.account,
            beginning_balance=Decimal(str(args.balance)),
            transaction_count=args.transactions
        )
        
        print(f"\nSuccess! Generated {args.transactions} transactions")
        print(f"Style: {args.style}")
        print(f"Output: {args.out}")
    
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()



