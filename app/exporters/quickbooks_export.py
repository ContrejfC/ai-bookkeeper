"""QuickBooks Online (QBO) and Xero export functionality."""
import csv
from typing import List, Dict, Any, TextIO
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.models import JournalEntryDB


class QuickBooksExporter:
    """Export journal entries to QuickBooks IIF format."""
    
    # Account type mapping
    ACCOUNT_TYPE_MAP = {
        "1000": "BANK",        # Cash at Bank
        "2000": "OCLIAB",      # Credit Card Payable
        "2100": "OCLIAB",      # Taxes Payable
        "6": "EXP",            # Expenses (6xxx)
        "7": "EXP",            # Marketing/Advertising
        "8": "INC",            # Income (8xxx)
    }
    
    @staticmethod
    def map_account_to_qbo(account: str) -> Dict[str, str]:
        """
        Map internal account to QuickBooks format.
        
        Args:
            account: Internal account string (e.g., "6100 Office Supplies")
            
        Returns:
            Dict with QBO account info
        """
        parts = account.split(maxsplit=1)
        account_num = parts[0] if parts else "9999"
        account_name = parts[1] if len(parts) > 1 else account
        
        # Determine account type based on account number
        first_digit = account_num[0] if account_num else "9"
        account_type = QuickBooksExporter.ACCOUNT_TYPE_MAP.get(
            account_num, 
            QuickBooksExporter.ACCOUNT_TYPE_MAP.get(first_digit, "OEXP")
        )
        
        return {
            "account_num": account_num,
            "account_name": account_name,
            "account_type": account_type
        }
    
    @staticmethod
    def export_to_iif(db: Session, output_file: TextIO, status: str = "posted"):
        """
        Export journal entries to QuickBooks IIF format.
        
        IIF format is a tab-delimited text file that QuickBooks can import.
        
        Args:
            db: Database session
            output_file: File object to write to
            status: Filter by status (posted, approved)
        """
        # Query journal entries
        query = db.query(JournalEntryDB)
        if status:
            query = query.filter(JournalEntryDB.status == status)
        
        jes = query.order_by(JournalEntryDB.date).all()
        
        if not jes:
            return
        
        # Write IIF header
        output_file.write("!TRNS\tTRNSID\tTRNSTYPE\tDATE\tACCNT\tAMOUNT\tMEMO\n")
        output_file.write("!SPL\tSPLID\tTRNSTYPE\tDATE\tACCNT\tAMOUNT\tMEMO\n")
        output_file.write("!ENDTRNS\n")
        
        # Write transactions
        for je in jes:
            date_str = je.date.strftime("%m/%d/%Y")
            memo = (je.memo or "")[:100]  # Truncate long memos
            
            # First line is the main transaction
            first_line = True
            total_amount = sum(line['debit'] - line['credit'] for line in je.lines)
            
            for line in je.lines:
                qbo_account = QuickBooksExporter.map_account_to_qbo(line['account'])
                amount = line['debit'] - line['credit']
                
                if first_line:
                    output_file.write(f"TRNS\t{je.je_id}\tGENERAL JOURNAL\t{date_str}\t{qbo_account['account_name']}\t{amount:.2f}\t{memo}\n")
                    first_line = False
                else:
                    output_file.write(f"SPL\t{je.je_id}\tGENERAL JOURNAL\t{date_str}\t{qbo_account['account_name']}\t{amount:.2f}\t{memo}\n")
            
            output_file.write("ENDTRNS\n")


class XeroExporter:
    """Export journal entries to Xero CSV format."""
    
    @staticmethod
    def map_account_to_xero(account: str) -> Dict[str, str]:
        """Map internal account to Xero format."""
        parts = account.split(maxsplit=1)
        account_code = parts[0] if parts else "800"
        account_name = parts[1] if len(parts) > 1 else account
        
        return {
            "account_code": account_code,
            "account_name": account_name
        }
    
    @staticmethod
    def export_to_csv(db: Session, output_file: TextIO, status: str = "posted"):
        """
        Export journal entries to Xero CSV format.
        
        Xero format: Journal Number, Date, Account Code, Account Name, Description, Debit, Credit
        
        Args:
            db: Database session
            output_file: File object to write to
            status: Filter by status
        """
        # Query journal entries
        query = db.query(JournalEntryDB)
        if status:
            query = query.filter(JournalEntryDB.status == status)
        
        jes = query.order_by(JournalEntryDB.date).all()
        
        # Write CSV
        writer = csv.writer(output_file)
        writer.writerow([
            "*JournalNumber",
            "*Date",
            "*AccountCode",
            "AccountName",
            "*Description",
            "Debit",
            "Credit",
            "TaxType",
            "TaxAmount",
            "TrackingName1",
            "TrackingOption1"
        ])
        
        for je in jes:
            date_str = je.date.strftime("%d/%m/%Y")
            description = (je.memo or "Automated entry")[:200]
            
            for line in je.lines:
                xero_account = XeroExporter.map_account_to_xero(line['account'])
                
                writer.writerow([
                    je.je_id,
                    date_str,
                    xero_account['account_code'],
                    xero_account['account_name'],
                    description,
                    f"{line['debit']:.2f}" if line['debit'] > 0 else "",
                    f"{line['credit']:.2f}" if line['credit'] > 0 else "",
                    "Tax Exempt",  # Default tax type
                    "0.00",
                    "",  # Tracking category 1
                    ""   # Tracking option 1
                ])


def export_to_quickbooks_iif(db: Session, file_path: str, status: str = "posted"):
    """Helper function to export to QuickBooks IIF file."""
    with open(file_path, 'w') as f:
        QuickBooksExporter.export_to_iif(db, f, status)


def export_to_xero_csv(db: Session, file_path: str, status: str = "posted"):
    """Helper function to export to Xero CSV file."""
    with open(file_path, 'w') as f:
        XeroExporter.export_to_csv(db, f, status)

