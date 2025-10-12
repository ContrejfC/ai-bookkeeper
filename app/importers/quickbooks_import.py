"""QuickBooks Online (QBO) and Xero import functionality."""
import csv
from typing import List, Dict, Any
from io import StringIO


class QuickBooksImporter:
    """Import chart of accounts from QuickBooks."""
    
    @staticmethod
    def parse_iif_accounts(content: str) -> List[Dict[str, str]]:
        """
        Parse chart of accounts from QuickBooks IIF format.
        
        Args:
            content: IIF file content
            
        Returns:
            List of account dicts
        """
        accounts = []
        lines = content.split('\n')
        
        in_account_section = False
        headers = []
        
        for line in lines:
            line = line.strip()
            
            if not line:
                continue
            
            if line.startswith('!ACCNT'):
                in_account_section = True
                headers = line.split('\t')[1:]  # Skip the !ACCNT marker
                continue
            
            if line.startswith('!END'):
                in_account_section = False
                continue
            
            if in_account_section and line.startswith('ACCNT'):
                parts = line.split('\t')[1:]  # Skip ACCNT marker
                
                if len(parts) >= len(headers):
                    account = {}
                    for i, header in enumerate(headers):
                        if i < len(parts):
                            account[header.lower()] = parts[i]
                    
                    # Map to internal format
                    if 'name' in account:
                        accounts.append({
                            'account_num': account.get('accnum', ''),
                            'account_name': account['name'],
                            'account_type': account.get('accnttype', 'EXP'),
                            'description': account.get('desc', ''),
                            'balance': float(account.get('balance', 0))
                        })
        
        return accounts
    
    @staticmethod
    def import_from_csv(content: str) -> List[Dict[str, str]]:
        """
        Import chart of accounts from generic CSV format.
        
        Expected columns: Account Number, Account Name, Account Type, Description
        
        Args:
            content: CSV file content
            
        Returns:
            List of account dicts
        """
        accounts = []
        reader = csv.DictReader(StringIO(content))
        
        for row in reader:
            account = {
                'account_num': row.get('Account Number', row.get('account_num', '')),
                'account_name': row.get('Account Name', row.get('account_name', '')),
                'account_type': row.get('Account Type', row.get('account_type', 'EXP')),
                'description': row.get('Description', row.get('description', '')),
                'balance': float(row.get('Balance', row.get('balance', 0)))
            }
            
            if account['account_name']:
                accounts.append(account)
        
        return accounts
    
    @staticmethod
    def map_to_internal_coa(accounts: List[Dict[str, str]]) -> List[str]:
        """
        Map external accounts to internal chart of accounts format.
        
        Args:
            accounts: List of account dicts from external system
            
        Returns:
            List of internal account strings
        """
        internal_accounts = []
        
        for account in accounts:
            account_num = account.get('account_num', '9999')
            account_name = account.get('account_name', 'Unknown')
            
            # Format: "XXXX Account Name"
            internal_account = f"{account_num} {account_name}"
            internal_accounts.append(internal_account)
        
        return internal_accounts


class XeroImporter:
    """Import chart of accounts from Xero."""
    
    @staticmethod
    def import_from_csv(content: str) -> List[Dict[str, str]]:
        """
        Import chart of accounts from Xero CSV export.
        
        Xero format: Account Code, Account Name, Type, Tax Type, Description
        
        Args:
            content: CSV file content
            
        Returns:
            List of account dicts
        """
        accounts = []
        reader = csv.DictReader(StringIO(content))
        
        for row in reader:
            account = {
                'account_num': row.get('Account Code', row.get('AccountCode', '')),
                'account_name': row.get('Account Name', row.get('AccountName', '')),
                'account_type': row.get('Type', 'EXPENSE'),
                'description': row.get('Description', ''),
                'tax_type': row.get('Tax Type', row.get('TaxType', ''))
            }
            
            if account['account_name']:
                accounts.append(account)
        
        return accounts
    
    @staticmethod
    def map_to_internal_coa(accounts: List[Dict[str, str]]) -> List[str]:
        """Map Xero accounts to internal format."""
        return QuickBooksImporter.map_to_internal_coa(accounts)

