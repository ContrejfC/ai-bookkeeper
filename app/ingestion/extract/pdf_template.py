"""
PDF Template Extractor
======================

Extract transactions from PDFs using bank-specific templates.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, date

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

from app.ingestion.extract.base import BaseExtractor, ExtractionContext, ExtractionResult
from app.ingestion.templates.registry import get_default_registry
from app.ingestion.utils.text_features import extract_text_features
from app.ingestion.schemas import CanonicalTransaction

logger = logging.getLogger(__name__)


class PDFTemplateExtractor(BaseExtractor):
    """
    PDF extractor that uses bank-specific templates for parsing.
    
    This extractor:
    1. Extracts text features from the PDF
    2. Matches features against known bank templates
    3. If a good match is found, uses template-specific parsing rules
    4. Falls back to generic extraction if no template matches
    """
    
    def __init__(self):
        super().__init__(name="pdf_template")
        self.registry = get_default_registry()
        logger.info(f"Loaded {len(self.registry)} bank templates")
    
    def can_handle(self, context: ExtractionContext) -> bool:
        """Check if this extractor can handle the file."""
        return context.mime_type == 'application/pdf' and HAS_PDFPLUMBER
    
    def extract(self, context: ExtractionContext) -> ExtractionResult:
        """
        Extract transactions using template matching.
        
        Args:
            context: Extraction context
        
        Returns:
            ExtractionResult with transactions and metadata
        """
        self.log_start(context)
        
        import time
        start_time = time.time()
        
        try:
            # Step 1: Extract text features
            features = extract_text_features(context.file_path)
            
            # Step 2: Match against templates
            best_match = self.registry.get_best_match(features)
            
            if best_match:
                logger.info(
                    f"Matched template: {best_match.template.name} "
                    f"(score: {best_match.score:.3f})"
                )
                
                # Step 3: Parse using template rules
                raw_transactions = self._parse_with_template(
                    context.file_path,
                    best_match.template,
                    context
                )
                
                result = ExtractionResult(
                    success=True,
                    raw_transactions=raw_transactions,
                    extraction_method="pdf_template",
                    confidence=best_match.score,
                    detected_bank=best_match.template.bank_name,
                    extraction_time_ms=int((time.time() - start_time) * 1000),
                    metadata={
                        'template_name': best_match.template.name,
                        'template_version': best_match.template.version,
                        'match_score': best_match.score,
                        'component_scores': best_match.component_scores,
                    }
                )
            else:
                logger.info("No template matched above threshold, falling back to generic extraction")
                
                # Fallback to generic table extraction
                raw_transactions = self._generic_table_extraction(context.file_path)
                
                result = ExtractionResult(
                    success=True,
                    raw_transactions=raw_transactions,
                    extraction_method="pdf_generic",
                    confidence=0.5,  # Lower confidence for generic extraction
                    extraction_time_ms=int((time.time() - start_time) * 1000),
                    metadata={'fallback': True}
                )
            
            self.log_end(result)
            return result
        
        except Exception as e:
            logger.error(f"PDF template extraction failed: {e}", exc_info=True)
            return self.create_error_result(str(e))
    
    def _parse_with_template(
        self,
        pdf_path: Path,
        template,
        context: ExtractionContext
    ) -> List[Dict[str, Any]]:
        """
        Parse PDF using template-specific rules.
        
        Args:
            pdf_path: Path to PDF
            template: Matched BankTemplate
            context: Extraction context
        
        Returns:
            List of raw transaction dictionaries
        """
        transactions = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                # Extract tables
                tables = page.extract_tables()
                
                for table in tables:
                    if not table or len(table) < 2:
                        continue
                    
                    # First row is typically headers
                    headers = table[0]
                    
                    # Map headers to canonical fields using template
                    column_map = self._map_columns(headers, template)
                    
                    # Process data rows
                    for row in table[1:]:
                        if not row or not any(row):
                            continue
                        
                        try:
                            txn = self._parse_row(
                                row,
                                column_map,
                                template,
                                context.account_hint or "UNKNOWN"
                            )
                            if txn:
                                transactions.append(txn)
                        except Exception as e:
                            logger.debug(f"Failed to parse row: {e}")
                            continue
        
        return transactions
    
    def _map_columns(self, headers: List[str], template) -> Dict[str, int]:
        """
        Map table columns to canonical fields.
        
        Args:
            headers: List of column headers from table
            template: BankTemplate
        
        Returns:
            Dict mapping canonical field names to column indices
        """
        column_map = {}
        
        # Clean headers
        clean_headers = [str(h).strip().lower() if h else '' for h in headers]
        
        # Try to find date column
        date_patterns = ['date', 'trans date', 'posting date', 'transaction date']
        for i, header in enumerate(clean_headers):
            if any(pattern in header for pattern in date_patterns):
                column_map['date'] = i
                break
        
        # Try to find description column
        desc_patterns = ['description', 'transaction', 'memo', 'details']
        for i, header in enumerate(clean_headers):
            if any(pattern in header for pattern in desc_patterns):
                column_map['description'] = i
                break
        
        # Try to find amount columns
        amount_patterns = ['amount', 'debit', 'credit', 'withdrawal', 'deposit']
        for i, header in enumerate(clean_headers):
            if 'amount' in header:
                column_map['amount'] = i
            elif any(p in header for p in ['debit', 'withdrawal', 'subtraction']):
                column_map['debit'] = i
            elif any(p in header for p in ['credit', 'deposit', 'addition']):
                column_map['credit'] = i
        
        # Try to find balance column
        balance_patterns = ['balance', 'running bal', 'ending balance']
        for i, header in enumerate(clean_headers):
            if any(pattern in header for pattern in balance_patterns):
                column_map['balance'] = i
                break
        
        return column_map
    
    def _parse_row(
        self,
        row: List[str],
        column_map: Dict[str, int],
        template,
        account_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Parse a single transaction row.
        
        Args:
            row: Row data
            column_map: Column index mapping
            template: BankTemplate
            account_id: Account identifier
        
        Returns:
            Transaction dictionary or None if parsing fails
        """
        # Extract date
        if 'date' not in column_map:
            return None
        
        date_str = str(row[column_map['date']]).strip() if row[column_map['date']] else ''
        if not date_str:
            return None
        
        post_date = self._parse_date(date_str, template.match.date_format_pref)
        if not post_date:
            return None
        
        # Extract description
        description = ''
        if 'description' in column_map:
            description = str(row[column_map['description']]).strip() if row[column_map['description']] else ''
        
        if not description:
            return None
        
        # Extract amount
        amount = self._parse_amount(row, column_map, template.match.amount_sign_rules)
        if amount is None:
            return None
        
        # Extract balance (optional)
        balance = None
        if 'balance' in column_map and row[column_map['balance']]:
            try:
                balance_str = str(row[column_map['balance']]).strip()
                balance = self._clean_amount(balance_str)
            except:
                pass
        
        return {
            'account_id': account_id,
            'post_date': post_date.isoformat(),
            'description': description,
            'amount': float(amount),
            'balance': float(balance) if balance else None,
            'currency': 'USD',  # Default, could be enhanced
        }
    
    def _parse_date(self, date_str: str, format_pref: str) -> Optional[date]:
        """Parse date string based on format preference."""
        import re
        from dateutil import parser as date_parser
        
        # Remove common noise
        date_str = re.sub(r'[^\d/\-\.]', ' ', date_str).strip()
        
        if not date_str:
            return None
        
        try:
            # Try dateutil parser (handles most formats)
            dt = date_parser.parse(date_str, dayfirst=(format_pref == 'DMY'))
            return dt.date()
        except:
            return None
    
    def _parse_amount(
        self,
        row: List[str],
        column_map: Dict[str, int],
        sign_rules: Dict[str, Any]
    ) -> Optional[Decimal]:
        """Parse amount from row using template sign rules."""
        amount = None
        
        # Case 1: Single amount column
        if 'amount' in column_map and row[column_map['amount']]:
            amount_str = str(row[column_map['amount']]).strip()
            amount = self._clean_amount(amount_str)
        
        # Case 2: Separate debit/credit columns
        elif 'debit' in column_map or 'credit' in column_map:
            debit = None
            credit = None
            
            if 'debit' in column_map and row[column_map['debit']]:
                debit_str = str(row[column_map['debit']]).strip()
                if debit_str:
                    debit = self._clean_amount(debit_str)
            
            if 'credit' in column_map and row[column_map['credit']]:
                credit_str = str(row[column_map['credit']]).strip()
                if credit_str:
                    credit = self._clean_amount(credit_str)
            
            # Combine (debits negative, credits positive)
            if debit is not None:
                amount = -abs(debit) if sign_rules.get('debit_is_negative', True) else debit
            elif credit is not None:
                amount = abs(credit)
        
        return amount
    
    def _clean_amount(self, amount_str: str) -> Optional[Decimal]:
        """Clean and parse amount string."""
        import re
        
        if not amount_str:
            return None
        
        # Remove currency symbols, commas
        amount_str = re.sub(r'[$,]', '', amount_str)
        
        # Handle parentheses for negative amounts
        is_negative = '(' in amount_str or ')' in amount_str
        amount_str = amount_str.replace('(', '').replace(')', '')
        
        # Remove extra spaces
        amount_str = amount_str.strip()
        
        if not amount_str or amount_str == '-':
            return None
        
        try:
            amount = Decimal(amount_str)
            if is_negative:
                amount = -abs(amount)
            return amount
        except:
            return None
    
    def _generic_table_extraction(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """
        Fallback generic table extraction when no template matches.
        
        Args:
            pdf_path: Path to PDF
        
        Returns:
            List of raw transaction dictionaries (best effort)
        """
        transactions = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                
                for table in tables:
                    if not table or len(table) < 2:
                        continue
                    
                    # Try to auto-detect columns
                    headers = table[0]
                    column_map = self._auto_detect_columns(headers)
                    
                    if not column_map.get('date') or not column_map.get('description'):
                        continue  # Skip if we can't find essential columns
                    
                    for row in table[1:]:
                        if not row or not any(row):
                            continue
                        
                        try:
                            # Very basic parsing
                            txn = {
                                'description': str(row[column_map.get('description', 0)]).strip(),
                                'raw_row': row  # Keep raw for debugging
                            }
                            
                            if column_map.get('date') is not None:
                                date_str = str(row[column_map['date']]).strip()
                                parsed_date = self._parse_date(date_str, 'MDY')
                                if parsed_date:
                                    txn['post_date'] = parsed_date.isoformat()
                            
                            transactions.append(txn)
                        except:
                            continue
        
        return transactions
    
    def _auto_detect_columns(self, headers: List[str]) -> Dict[str, int]:
        """Auto-detect column purposes from headers."""
        column_map = {}
        
        clean_headers = [str(h).strip().lower() if h else '' for h in headers]
        
        for i, header in enumerate(clean_headers):
            if 'date' in header:
                column_map['date'] = i
            elif any(kw in header for kw in ['description', 'transaction', 'memo']):
                column_map['description'] = i
            elif 'amount' in header:
                column_map['amount'] = i
            elif 'balance' in header:
                column_map['balance'] = i
        
        return column_map



