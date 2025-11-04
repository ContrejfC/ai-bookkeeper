"""
OFX/QFX Normalizer
==================

Parse and normalize OFX/QFX (Open Financial Exchange) files to canonical schema.
Handles both SGML and XML OFX formats.
"""

import logging
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional
from ofxparse import OfxParser
from ofxparse.ofxparse import Account, Transaction as OfxTransaction

from app.ingestion.config import config
from app.ingestion.errors import ParseFailedError, TooManyRowsError
from app.ingestion.schemas import CanonicalTransaction

logger = logging.getLogger(__name__)


class OFXNormalizer:
    """
    Normalize OFX/QFX files to canonical format.
    
    Features:
    - Parse both SGML and XML OFX formats
    - Handle banking and credit card statements
    - Proper polarity handling (debits/credits)
    - Extract account information
    """
    
    def __init__(self, file_path: str):
        """
        Initialize OFX normalizer.
        
        Args:
            file_path: Path to OFX/QFX file
        """
        self.file_path = file_path
        self.ofx = None
        
    def _parse_ofx(self) -> None:
        """Parse OFX file."""
        try:
            with open(self.file_path, 'rb') as f:
                self.ofx = OfxParser.parse(f)
            
            logger.debug(f"Parsed OFX file: {self.file_path}")
            
        except Exception as e:
            raise ParseFailedError("ofx", f"Failed to parse OFX: {e}")
    
    def _determine_polarity(self, txn: OfxTransaction, account_type: str) -> Decimal:
        """
        Determine transaction polarity (sign).
        
        OFX amounts can be positive or negative. Convention:
        - Banking accounts: negative = debit (payment), positive = credit (deposit)
        - Credit cards: negative = charge, positive = payment
        
        Args:
            txn: OFX transaction
            account_type: Account type (e.g., 'CHECKING', 'CREDITCARD')
        
        Returns:
            Signed amount
        """
        amount = Decimal(str(txn.amount))
        
        # OFX already has correct sign convention
        # Just ensure it's a Decimal
        return amount
    
    def _parse_ofx_date(self, ofx_date) -> date:
        """
        Parse OFX date to Python date.
        
        OFX dates can be datetime objects or strings.
        
        Args:
            ofx_date: OFX date field
        
        Returns:
            Python date object
        """
        if isinstance(ofx_date, datetime):
            return ofx_date.date()
        elif isinstance(ofx_date, date):
            return ofx_date
        elif isinstance(ofx_date, str):
            # Try parsing string
            try:
                return datetime.strptime(ofx_date[:8], '%Y%m%d').date()
            except ValueError:
                pass
        
        raise ValueError(f"Cannot parse OFX date: {ofx_date}")
    
    def normalize(self, account_hint: Optional[str] = None) -> List[CanonicalTransaction]:
        """
        Normalize OFX file to canonical transactions.
        
        Args:
            account_hint: Optional account number hint (ignored if OFX has account info)
        
        Returns:
            List of canonical transactions
        """
        logger.info(f"Normalizing OFX: {self.file_path}")
        
        # Parse OFX
        self._parse_ofx()
        
        if not self.ofx:
            raise ParseFailedError("ofx", "No OFX data parsed")
        
        all_transactions = []
        
        # Process each account in the OFX file
        accounts = []
        
        # Check for bank accounts
        if hasattr(self.ofx, 'accounts') and self.ofx.accounts:
            accounts.extend(self.ofx.accounts)
        
        # Check for credit card accounts
        if hasattr(self.ofx, 'credit_cards') and self.ofx.credit_cards:
            accounts.extend(self.ofx.credit_cards)
        
        if not accounts:
            logger.warning("No accounts found in OFX file")
            return []
        
        # Process each account
        for account in accounts:
            try:
                account_txns = self._process_account(account, account_hint)
                all_transactions.extend(account_txns)
            except Exception as e:
                logger.error(f"Failed to process account: {e}")
                continue
        
        logger.info(f"Parsed {len(all_transactions)} transactions from OFX")
        
        return all_transactions
    
    def _process_account(
        self,
        account: Account,
        account_hint: Optional[str]
    ) -> List[CanonicalTransaction]:
        """
        Process transactions from a single account.
        
        Args:
            account: OFX account object
            account_hint: Optional account hint
        
        Returns:
            List of canonical transactions
        """
        transactions = []
        
        # Get account information
        account_id = account_hint or getattr(account, 'account_id', 'unknown')
        account_type = getattr(account, 'account_type', 'CHECKING')
        
        # Get currency (default to USD)
        currency = getattr(account, 'curdef', 'USD')
        if not currency:
            currency = 'USD'
        
        # Get statement information
        statement = getattr(account, 'statement', None)
        if not statement:
            logger.warning(f"No statement found for account {account_id}")
            return []
        
        # Get balance (optional)
        balance_amount = None
        if hasattr(statement, 'balance'):
            balance_amount = Decimal(str(statement.balance))
        
        # Process transactions
        ofx_transactions = getattr(statement, 'transactions', [])
        
        if not ofx_transactions:
            logger.warning(f"No transactions in statement for account {account_id}")
            return []
        
        # Check row limit
        if len(ofx_transactions) > config.MAX_TRANSACTIONS_PER_FILE:
            raise TooManyRowsError(len(ofx_transactions), config.MAX_TRANSACTIONS_PER_FILE)
        
        for ofx_txn in ofx_transactions:
            try:
                txn = self._parse_ofx_transaction(
                    ofx_txn,
                    account_id,
                    account_type,
                    currency,
                    balance_amount
                )
                if txn:
                    transactions.append(txn)
            except Exception as e:
                logger.warning(f"Failed to parse OFX transaction: {e}")
                continue
        
        return transactions
    
    def _parse_ofx_transaction(
        self,
        ofx_txn: OfxTransaction,
        account_id: str,
        account_type: str,
        currency: str,
        statement_balance: Optional[Decimal]
    ) -> Optional[CanonicalTransaction]:
        """
        Parse a single OFX transaction to canonical format.
        
        Args:
            ofx_txn: OFX transaction object
            account_id: Account identifier
            account_type: Account type
            currency: Currency code
            statement_balance: Statement ending balance (if available)
        
        Returns:
            CanonicalTransaction or None
        """
        # Parse date
        try:
            post_date = self._parse_ofx_date(ofx_txn.date)
        except ValueError as e:
            logger.warning(f"Invalid OFX transaction date: {e}")
            return None
        
        # Get description/memo
        description = ofx_txn.payee or ofx_txn.memo or "Unknown"
        if ofx_txn.payee and ofx_txn.memo and ofx_txn.payee != ofx_txn.memo:
            description = f"{ofx_txn.payee} - {ofx_txn.memo}"
        
        # Get amount with proper polarity
        amount = self._determine_polarity(ofx_txn, account_type)
        
        # Get transaction ID (reference)
        reference = getattr(ofx_txn, 'id', None) or getattr(ofx_txn, 'fitid', None)
        
        # Get transaction type (category)
        category = getattr(ofx_txn, 'type', None)
        
        # Check for posted date vs user date
        value_date = None
        if hasattr(ofx_txn, 'user_date') and ofx_txn.user_date:
            try:
                value_date = self._parse_ofx_date(ofx_txn.user_date)
            except ValueError:
                pass
        
        # Balance is typically not per-transaction in OFX
        # Could be calculated if needed
        balance = None
        
        return CanonicalTransaction(
            account_id=account_id,
            post_date=post_date,
            value_date=value_date,
            description=description.strip(),
            amount=amount,
            balance=balance,
            currency=currency,
            source="ofx",
            source_confidence=0.92,  # OFX is structured, high confidence
            reference=reference,
            category=category
        )


def normalize_ofx(
    file_path: str,
    account_hint: Optional[str] = None
) -> List[CanonicalTransaction]:
    """
    Convenience function to normalize an OFX file.
    
    Args:
        file_path: Path to OFX/QFX file
        account_hint: Optional account number hint
    
    Returns:
        List of canonical transactions
    """
    normalizer = OFXNormalizer(file_path)
    return normalizer.normalize(account_hint=account_hint)



