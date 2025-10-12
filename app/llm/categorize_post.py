"""LLM-powered categorization and posting."""
import json
import logging
from typing import Dict, Any, List, Optional
import openai
from config.settings import settings
from app.db.models import Transaction, JournalEntry, JournalEntryLine
from app.llm.prompts import SYSTEM_PROMPT, CATEGORIZATION_FUNCTION, format_categorization_prompt

logger = logging.getLogger(__name__)


class LLMCategorizer:
    """LLM-powered transaction categorizer."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the LLM categorizer.
        
        Args:
            api_key: OpenAI API key (uses settings if not provided)
        """
        self.api_key = api_key or settings.openai_api_key
        if self.api_key:
            openai.api_key = self.api_key
        self.model = settings.llm_model
    
    def categorize_transaction(
        self,
        transaction: Transaction,
        chart_of_accounts: List[str],
        historical_mappings: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Categorize a transaction using LLM with function calling.
        
        Args:
            transaction: Transaction to categorize
            chart_of_accounts: List of available accounts
            historical_mappings: Historical counterparty->account mappings
            
        Returns:
            Dict with account, journal_entry, confidence, needs_review, rationale
        """
        if not self.api_key:
            logger.warning("No OpenAI API key configured, using fallback")
            return self._fallback_categorization(transaction, chart_of_accounts)
        
        historical_mappings = historical_mappings or []
        
        # Format the prompt
        user_prompt = format_categorization_prompt(
            transaction.model_dump(),
            chart_of_accounts,
            historical_mappings
        )
        
        try:
            # Call OpenAI with function calling
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                functions=[CATEGORIZATION_FUNCTION],
                function_call={"name": "categorize_and_post"},
                temperature=0.3
            )
            
            # Extract function call result
            message = response.choices[0].message
            
            if message.function_call:
                result = json.loads(message.function_call.arguments)
                
                # Validate balance
                je_data = result['journal_entry']
                total_debits = sum(line['debit'] for line in je_data['lines'])
                total_credits = sum(line['credit'] for line in je_data['lines'])
                
                if abs(total_debits - total_credits) > 0.01:
                    logger.warning(f"Unbalanced JE from LLM: debits={total_debits}, credits={total_credits}")
                    result['needs_review'] = True
                    result['rationale'] = f"UNBALANCED ENTRY (off by {abs(total_debits - total_credits):.2f}). " + result.get('rationale', '')
                
                return result
            else:
                logger.warning("No function call in LLM response")
                return self._fallback_categorization(transaction, chart_of_accounts)
                
        except Exception as e:
            logger.error(f"LLM categorization failed: {e}")
            return self._fallback_categorization(transaction, chart_of_accounts)
    
    def _fallback_categorization(
        self,
        transaction: Transaction,
        chart_of_accounts: List[str]
    ) -> Dict[str, Any]:
        """
        Fallback categorization when LLM is unavailable.
        
        Uses simple heuristics based on amount sign.
        """
        amount = abs(transaction.amount)
        
        if transaction.amount > 0:
            # Revenue
            account = "8000 Sales Revenue"
            lines = [
                {"account": "1000 Cash at Bank", "debit": amount, "credit": 0.0},
                {"account": account, "debit": 0.0, "credit": amount}
            ]
        else:
            # Expense
            account = "6999 Miscellaneous Expense"
            lines = [
                {"account": account, "debit": amount, "credit": 0.0},
                {"account": "1000 Cash at Bank", "debit": 0.0, "credit": amount}
            ]
        
        return {
            "account": account,
            "journal_entry": {
                "date": transaction.date,
                "lines": lines
            },
            "confidence": 0.3,
            "needs_review": True,
            "rationale": "Fallback: LLM unavailable or failed"
        }
    
    def create_journal_entry(
        self,
        transaction: Transaction,
        llm_result: Dict[str, Any]
    ) -> JournalEntry:
        """
        Create a JournalEntry object from LLM result.
        
        Args:
            transaction: Source transaction
            llm_result: LLM categorization result
            
        Returns:
            JournalEntry object
        """
        import uuid
        
        je_data = llm_result['journal_entry']
        
        # Parse lines
        lines = [
            JournalEntryLine(**line)
            for line in je_data['lines']
        ]
        
        # Create JournalEntry
        je = JournalEntry(
            je_id=f"je_{uuid.uuid4().hex[:16]}",
            date=je_data['date'],
            lines=lines,
            source_txn_id=transaction.txn_id,
            memo=llm_result.get('rationale', ''),
            confidence=llm_result.get('confidence', 0.0),
            status="proposed",
            needs_review=llm_result.get('needs_review', False) or llm_result.get('confidence', 0.0) < settings.confidence_threshold
        )
        
        # Force review if unbalanced
        if not je.is_balanced():
            je.needs_review = True
            logger.warning(f"Unbalanced JE created: {je.je_id}, diff={je.get_balance_diff():.2f}")
        
        return je


# Global instance
llm_categorizer = LLMCategorizer()

