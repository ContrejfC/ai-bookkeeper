#!/usr/bin/env python3
"""
Generate Test Bank Statement PDF
=================================

Creates a realistic-looking bank statement PDF for testing the drag-and-drop upload.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from datetime import datetime, timedelta
import random

def generate_test_bank_statement(output_path="test_bank_statement.pdf"):
    """Generate a realistic test bank statement PDF"""
    
    # Create PDF
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#003366'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#666666'),
        alignment=TA_LEFT
    )
    
    # Bank Header
    story.append(Paragraph("FIRST NATIONAL BANK", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Account Information
    account_info = [
        ["Account Holder:", "John Smith"],
        ["Account Number:", "****1234"],
        ["Account Type:", "Business Checking"],
        ["Statement Period:", "October 1, 2024 - October 31, 2024"],
        ["Statement Date:", "November 1, 2024"]
    ]
    
    account_table = Table(account_info, colWidths=[2*inch, 4*inch])
    account_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#666666')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(account_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Summary Box
    summary_data = [
        ["Beginning Balance:", "$12,458.32"],
        ["Total Deposits:", "$8,245.00"],
        ["Total Withdrawals:", "$-6,892.18"],
        ["Ending Balance:", "$13,811.14"]
    ]
    
    summary_table = Table(summary_data, colWidths=[2.5*inch, 1.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f0f0')),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('PADDING', (0, 0), (-1, -1), 10),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
        ('LINEBELOW', (0, 2), (-1, 2), 2, colors.HexColor('#666666')),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.4*inch))
    
    # Transaction Header
    story.append(Paragraph("<b>TRANSACTION HISTORY</b>", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))
    
    # Generate realistic transactions
    transactions = []
    transactions.append(['Date', 'Description', 'Debit', 'Credit', 'Balance'])
    
    balance = 12458.32
    base_date = datetime(2024, 10, 1)
    
    # Sample transactions
    sample_txns = [
        ("ACH DEPOSIT - PAYROLL", 5245.00, "credit"),
        ("AMAZON.COM", -127.45, "debit"),
        ("SQUARE *COFFEE SHOP", -4.50, "debit"),
        ("STRIPE PAYMENT", 3000.00, "credit"),
        ("GOOGLE WORKSPACE", -12.00, "debit"),
        ("OFFICE DEPOT", -234.67, "debit"),
        ("ELECTRIC COMPANY", -156.89, "debit"),
        ("VERIZON WIRELESS", -89.99, "debit"),
        ("FEDEX", -45.20, "debit"),
        ("LINKEDIN ADS", -250.00, "debit"),
        ("STAPLES", -67.43, "debit"),
        ("ZOOM.US", -14.99, "debit"),
        ("QUICKBOOKS ONLINE", -50.00, "debit"),
        ("DROPBOX", -9.99, "debit"),
        ("UBER", -32.15, "debit"),
        ("SHELL GAS STATION", -48.50, "debit"),
        ("CLIENT PAYMENT", 2500.00, "credit"),
        ("INSURANCE PREMIUM", -450.00, "debit"),
        ("COMCAST", -79.99, "debit"),
        ("FREELANCER.COM", -850.00, "debit"),
    ]
    
    for i, (desc, amount, txn_type) in enumerate(sample_txns):
        date = base_date + timedelta(days=random.randint(0, 30))
        date_str = date.strftime("%m/%d/%Y")
        
        if txn_type == "credit":
            balance += amount
            transactions.append([
                date_str,
                desc,
                "",
                f"${amount:,.2f}",
                f"${balance:,.2f}"
            ])
        else:
            balance += amount  # amount is already negative
            transactions.append([
                date_str,
                desc,
                f"${abs(amount):,.2f}",
                "",
                f"${balance:,.2f}"
            ])
    
    # Sort by date
    transactions[1:] = sorted(transactions[1:], key=lambda x: datetime.strptime(x[0], "%m/%d/%Y"))
    
    # Create transaction table
    txn_table = Table(transactions, colWidths=[1*inch, 2.5*inch, 1*inch, 1*inch, 1.2*inch])
    txn_table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        
        # Data rows
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),  # Date
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),  # Description
        ('ALIGN', (2, 1), (2, -1), 'RIGHT'), # Debit
        ('ALIGN', (3, 1), (3, -1), 'RIGHT'), # Credit
        ('ALIGN', (4, 1), (4, -1), 'RIGHT'), # Balance
        
        # Alternating row colors
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
        
        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#666666')),
        
        # Padding
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(txn_table)
    story.append(Spacer(1, 0.4*inch))
    
    # Footer
    footer_text = """
    <para align=center>
    <font size=8 color="#666666">
    First National Bank • 123 Main Street, Anytown, USA 12345<br/>
    Customer Service: 1-800-555-0123 • www.firstnationalbank.com<br/>
    Member FDIC • Equal Housing Lender
    </font>
    </para>
    """
    story.append(Paragraph(footer_text, styles['Normal']))
    
    # Build PDF
    doc.build(story)
    print(f"✅ Test bank statement generated: {output_path}")
    return output_path

if __name__ == "__main__":
    # Generate the PDF
    output_file = "test_bank_statement.pdf"
    generate_test_bank_statement(output_file)
    print(f"\n📄 Test bank statement created successfully!")
    print(f"📍 Location: {output_file}")
    print(f"\n💡 You can now upload this PDF to test the drag-and-drop feature at:")
    print(f"   https://ai-bookkeeper-nine.vercel.app/free/categorizer")

