"""
CSV Normalizer
==============

Parse and normalize CSV bank statements to canonical transaction schema.
Auto-detects delimiter, encoding, headers, and locale.
"""

import csv
import logging
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from typing import List, Dict, Any, Tuple, Optional
from io import StringIO
import chardet

from app.ingestion.config import config
from app.ingestion.errors import (
    ParseFailedError,
    LocaleAmbiguousError,
    MissingRequiredFieldError,
    InvalidDataFormatError,
    TooManyRowsError
)
from app.ingestion.schemas import CanonicalTransaction

logger = logging.getLogger(__name__)


# Common CSV header mappings (case-insensitive)
HEADER_MAPPINGS = {
    'post_date': [
        'date', 'post date', 'posting date', 'transaction date', 'trans date',
        'posted', 'posted date', 'trans. date', 'datetime'
    ],
    'value_date': [
        'value date', 'effective date', 'settlement date'
    ],
    'description': [
        'description', 'memo', 'details', 'transaction details', 'narrative',
        'payee', 'merchant', 'vendor', 'reference', 'desc'
    ],
    'amount': [
        'amount', 'transaction amount', 'value', 'trans amount', 'sum'
    ],
    'debit': [
        'debit', 'debits', 'withdrawal', 'withdrawals', 'debit amount',
        'payment', 'payments', 'out'
    ],
    'credit': [
        'credit', 'credits', 'deposit', 'deposits', 'credit amount',
        'receipt', 'receipts', 'in'
    ],
    'balance': [
        'balance', 'running balance', 'account balance', 'balance amount',
        'ending balance', 'current balance'
    ],
    'account_id': [
        'account', 'account number', 'account #', 'acct', 'account id'
    ],
    'reference': [
        'reference', 'ref', 'transaction id', 'txn id', 'check number',
        'cheque number', 'confirmation', 'conf number'
    ],
    'category': [
        'category', 'type', 'transaction type', 'class', 'classification'
    ]
}


class CSVNormalizer:
    """
    Normalize CSV bank statements to canonical format.
    
    Features:
    - Auto-detect delimiter (comma, semicolon, tab, pipe)
    - Auto-detect encoding (UTF-8, Latin-1, CP1252)
    - Smart header mapping
    - Locale/currency detection
    - Date format detection
    - Debit/credit polarity handling
    """
    
    def __init__(self, file_path: str, encoding: Optional[str] = None):
        """
        Initialize CSV normalizer.
        
        Args:
            file_path: Path to CSV file
            encoding: Optional encoding (auto-detected if None)
        """
        self.file_path = file_path
        self.encoding = encoding or self._detect_encoding()
        self.delimiter = None
        self.headers = []
        self.header_map = {}
        self.date_format = None
        self.has_separate_debit_credit = False
        
    def _detect_encoding(self) -> str:
        """Detect file encoding."""
        try:
            with open(self.file_path, 'rb') as f:
                raw_data = f.read(8192)  # Read first 8KB
            
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            confidence = result['confidence']
            
            logger.debug(f"Detected encoding: {encoding} (confidence: {confidence:.2f})")
            
            # Fallback to UTF-8 if confidence is low
            if confidence < 0.7:
                logger.warning(f"Low encoding confidence, defaulting to UTF-8")
                return 'utf-8'
            
            return encoding or 'utf-8'
        
        except Exception as e:
            logger.error(f"Encoding detection failed: {e}, defaulting to UTF-8")
            return 'utf-8'
    
    def _detect_delimiter(self, sample_lines: List[str]) -> str:
        """
        Detect CSV delimiter.
        
        Args:
            sample_lines: First few lines of CSV
        
        Returns:
            Detected delimiter
        """
        delimiters = [',', ';', '\t', '|']
        scores = {}
        
        for delimiter in delimiters:
            # Count occurrences in each line
            counts = [line.count(delimiter) for line in sample_lines[:5]]
            
            # Good delimiter has consistent counts
            if counts:
                avg_count = sum(counts) / len(counts)
                variance = sum((c - avg_count) ** 2 for c in counts) / len(counts)
                
                # Score: prefer higher average, lower variance
                scores[delimiter] = avg_count - variance if avg_count > 0 else 0
        
        # Pick delimiter with highest score
        best_delimiter = max(scores, key=scores.get)
        
        logger.debug(f"Detected delimiter: {repr(best_delimiter)} (scores: {scores})")
        
        return best_delimiter
    
    def _map_headers(self, raw_headers: List[str]) -> Dict[str, str]:
        """
        Map raw CSV headers to canonical field names.
        
        Args:
            raw_headers: Raw header names from CSV
        
        Returns:
            Dictionary mapping canonical names to CSV column names
        """
        header_map = {}
        
        # Normalize headers (lowercase, strip whitespace)
        normalized_headers = {
            h.lower().strip(): h for h in raw_headers
        }
        
        # Try to map each canonical field
        for canonical, variations in HEADER_MAPPINGS.items():
            for variation in variations:
                if variation in normalized_headers:
                    header_map[canonical] = normalized_headers[variation]
                    logger.debug(f"Mapped '{variation}' -> '{canonical}'")
                    break
        
        # Check if we have separate debit/credit columns
        self.has_separate_debit_credit = 'debit' in header_map and 'credit' in header_map
        
        return header_map
    
    def _parse_date(self, date_str: str, formats: List[str] = None) -> date:
        """
        Parse date string with multiple format attempts.
        
        Args:
            date_str: Date string
            formats: Optional list of formats to try
        
        Returns:
            Parsed date object
        """
        if not date_str or not date_str.strip():
            raise ValueError("Empty date string")
        
        # Common date formats
        if formats is None:
            formats = [
                '%Y-%m-%d',      # 2024-10-30
                '%m/%d/%Y',      # 10/30/2024
                '%d/%m/%Y',      # 30/10/2024
                '%Y/%m/%d',      # 2024/10/30
                '%m-%d-%Y',      # 10-30-2024
                '%d-%m-%Y',      # 30-10-2024
                '%m/%d/%y',      # 10/30/24
                '%d/%m/%y',      # 30/10/24
                '%b %d, %Y',     # Oct 30, 2024
                '%d %b %Y',      # 30 Oct 2024
                '%B %d, %Y',     # October 30, 2024
            ]
        
        date_str = date_str.strip()
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        raise ValueError(f"Could not parse date: {date_str}")
    
    def _parse_amount(self, amount_str: str) -> Decimal:
        """
        Parse amount string to Decimal.
        
        Handles:
        - Thousands separators (comma, period, space)
        - Decimal separators (period, comma)
        - Currency symbols
        - Parentheses for negative amounts
        
        Args:
            amount_str: Amount string
        
        Returns:
            Parsed Decimal amount
        """
        if not amount_str or not amount_str.strip():
            raise ValueError("Empty amount string")
        
        original = amount_str
        amount_str = amount_str.strip()
        
        # Check for parentheses (negative)
        is_negative = amount_str.startswith('(') and amount_str.endswith(')')
        if is_negative:
            amount_str = amount_str[1:-1]
        
        # Remove currency symbols
        for symbol in ['$', '£', '€', '¥', 'USD', 'GBP', 'EUR', 'JPY']:
            amount_str = amount_str.replace(symbol, '')
        
        amount_str = amount_str.strip()
        
        # Detect decimal separator
        # If comma is last separator, it's likely decimal
        # If period is last separator, it's likely decimal
        last_comma = amount_str.rfind(',')
        last_period = amount_str.rfind('.')
        
        if last_comma > last_period:
            # European format: 1.234,56
            amount_str = amount_str.replace('.', '')  # Remove thousands separator
            amount_str = amount_str.replace(',', '.')  # Comma is decimal
        else:
            # US format: 1,234.56
            amount_str = amount_str.replace(',', '')  # Remove thousands separator
        
        # Remove spaces
        amount_str = amount_str.replace(' ', '')
        
        try:
            amount = Decimal(amount_str)
            if is_negative:
                amount = -amount
            return amount
        except InvalidOperation:
            raise ValueError(f"Could not parse amount: {original}")
    
    def normalize(self, account_hint: Optional[str] = None) -> List[CanonicalTransaction]:
        """
        Normalize CSV file to canonical transactions.
        
        Args:
            account_hint: Optional account number hint
        
        Returns:
            List of canonical transactions
        """
        logger.info(f"Normalizing CSV: {self.file_path}")
        
        # Read file
        try:
            with open(self.file_path, 'r', encoding=self.encoding, errors='replace') as f:
                content = f.read()
        except Exception as e:
            raise ParseFailedError("csv", f"Failed to read file: {e}")
        
        # Detect delimiter
        lines = content.split('\n')
        self.delimiter = self._detect_delimiter(lines)
        
        # Parse CSV
        try:
            reader = csv.DictReader(
                StringIO(content),
                delimiter=self.delimiter
            )
            
            self.headers = reader.fieldnames or []
            if not self.headers:
                raise ParseFailedError("csv", "No headers found")
            
            # Map headers
            self.header_map = self._map_headers(self.headers)
            
            # Validate required fields
            if 'post_date' not in self.header_map:
                raise MissingRequiredFieldError('post_date or date')
            
            if 'description' not in self.header_map:
                raise MissingRequiredFieldError('description or memo')
            
            if 'amount' not in self.header_map and not self.has_separate_debit_credit:
                raise MissingRequiredFieldError('amount or debit/credit columns')
            
            # Parse rows
            transactions = []
            row_count = 0
            
            for row in reader:
                row_count += 1
                
                # Check row limit
                if row_count > config.MAX_CSV_ROWS:
                    raise TooManyRowsError(row_count, config.MAX_CSV_ROWS)
                
                # Skip empty rows
                if not any(row.values()):
                    continue
                
                try:
                    txn = self._parse_row(row, account_hint)
                    if txn:
                        transactions.append(txn)
                except Exception as e:
                    logger.warning(f"Failed to parse row {row_count}: {e}")
                    continue
            
            logger.info(f"Parsed {len(transactions)} transactions from CSV")
            
            return transactions
        
        except csv.Error as e:
            raise ParseFailedError("csv", f"CSV parsing error: {e}")
        except Exception as e:
            if isinstance(e, (ParseFailedError, MissingRequiredFieldError, TooManyRowsError)):
                raise
            raise ParseFailedError("csv", f"Unexpected error: {e}")
    
    def _parse_row(self, row: Dict[str, str], account_hint: Optional[str]) -> Optional[CanonicalTransaction]:
        """
        Parse a single CSV row to canonical transaction.
        
        Args:
            row: CSV row as dictionary
            account_hint: Optional account hint
        
        Returns:
            CanonicalTransaction or None if row should be skipped
        """
        # Extract fields using header map
        post_date_str = row.get(self.header_map.get('post_date', ''), '').strip()
        description = row.get(self.header_map.get('description', ''), '').strip()
        
        # Skip rows with empty key fields
        if not post_date_str or not description:
            return None
        
        # Parse date
        try:
            post_date = self._parse_date(post_date_str)
        except ValueError as e:
            logger.warning(f"Invalid date '{post_date_str}': {e}")
            return None
        
        # Parse value date (optional)
        value_date = None
        if 'value_date' in self.header_map:
            value_date_str = row.get(self.header_map['value_date'], '').strip()
            if value_date_str:
                try:
                    value_date = self._parse_date(value_date_str)
                except ValueError:
                    pass
        
        # Parse amount
        if self.has_separate_debit_credit:
            # Separate debit/credit columns
            debit_str = row.get(self.header_map['debit'], '').strip()
            credit_str = row.get(self.header_map['credit'], '').strip()
            
            if debit_str:
                amount = -self._parse_amount(debit_str)  # Debits are negative
            elif credit_str:
                amount = self._parse_amount(credit_str)  # Credits are positive
            else:
                logger.warning("Row has no debit or credit amount")
                return None
        else:
            # Single amount column
            amount_str = row.get(self.header_map['amount'], '').strip()
            if not amount_str:
                return None
            amount = self._parse_amount(amount_str)
        
        # Parse balance (optional)
        balance = None
        if 'balance' in self.header_map:
            balance_str = row.get(self.header_map['balance'], '').strip()
            if balance_str:
                try:
                    balance = self._parse_amount(balance_str)
                except ValueError:
                    pass
        
        # Get account ID
        account_id = account_hint or "unknown"
        if 'account_id' in self.header_map:
            acc = row.get(self.header_map['account_id'], '').strip()
            if acc:
                account_id = acc
        
        # Get reference (optional)
        reference = None
        if 'reference' in self.header_map:
            reference = row.get(self.header_map['reference'], '').strip()
        
        # Get category (optional)
        category = None
        if 'category' in self.header_map:
            category = row.get(self.header_map['category'], '').strip()
        
        # Create canonical transaction
        return CanonicalTransaction(
            account_id=account_id,
            post_date=post_date,
            value_date=value_date,
            description=description,
            amount=amount,
            balance=balance,
            currency="USD",  # TODO: Detect from data
            source="csv",
            source_confidence=0.88,  # Base confidence for CSV
            reference=reference,
            category=category
        )


def normalize_csv(
    file_path: str,
    account_hint: Optional[str] = None,
    encoding: Optional[str] = None
) -> List[CanonicalTransaction]:
    """
    Convenience function to normalize a CSV file.
    
    Args:
        file_path: Path to CSV file
        account_hint: Optional account number hint
        encoding: Optional encoding
    
    Returns:
        List of canonical transactions
    """
    normalizer = CSVNormalizer(file_path, encoding=encoding)
    return normalizer.normalize(account_hint=account_hint)



