"""System prompts for LLM categorization."""

SYSTEM_PROMPT = """You are an accounting assistant. Follow U.S. GAAP and double-entry.
Return ONLY valid JSON for the function call. Use the provided Chart of Accounts.
If uncertain, set "needs_review": true and explain briefly in "rationale".
Ensure journal entries are balanced; otherwise force review."""


CATEGORIZATION_FUNCTION = {
    "name": "categorize_and_post",
    "description": "Categorize a bank transaction and create a balanced journal entry",
    "parameters": {
        "type": "object",
        "properties": {
            "account": {
                "type": "string",
                "description": "The primary expense/revenue account to post to (from Chart of Accounts)"
            },
            "journal_entry": {
                "type": "object",
                "description": "The complete journal entry with balanced debits and credits",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format"
                    },
                    "lines": {
                        "type": "array",
                        "description": "Array of journal entry lines. Must balance (debits = credits).",
                        "items": {
                            "type": "object",
                            "properties": {
                                "account": {
                                    "type": "string",
                                    "description": "Account name from Chart of Accounts"
                                },
                                "debit": {
                                    "type": "number",
                                    "description": "Debit amount (0 if credit entry)"
                                },
                                "credit": {
                                    "type": "number",
                                    "description": "Credit amount (0 if debit entry)"
                                }
                            },
                            "required": ["account", "debit", "credit"]
                        }
                    }
                },
                "required": ["date", "lines"]
            },
            "confidence": {
                "type": "number",
                "description": "Confidence score from 0.0 to 1.0"
            },
            "needs_review": {
                "type": "boolean",
                "description": "Whether this entry needs human review"
            },
            "rationale": {
                "type": "string",
                "description": "Brief explanation of the categorization decision"
            }
        },
        "required": ["account", "journal_entry", "confidence", "needs_review", "rationale"]
    }
}


def format_categorization_prompt(
    transaction: dict,
    chart_of_accounts: list,
    historical_mappings: list
) -> str:
    """
    Format the user prompt for LLM categorization.
    
    Args:
        transaction: Transaction dict
        chart_of_accounts: List of account names
        historical_mappings: List of historical counterparty->account mappings
        
    Returns:
        Formatted prompt string
    """
    hist_text = ""
    if historical_mappings:
        hist_text = "\n\nHistorical mappings for similar vendors:\n"
        for mapping in historical_mappings[:5]:
            hist_text += f"- {mapping.get('counterparty', 'Unknown')}: {mapping.get('account', 'Unknown')}\n"
    
    prompt = f"""Categorize this bank transaction and create a balanced journal entry.

Transaction:
- Date: {transaction.get('date')}
- Amount: ${transaction.get('amount')}
- Description: {transaction.get('description')}
- Counterparty: {transaction.get('counterparty', 'Unknown')}

Chart of Accounts (use these exact names):
{chr(10).join(f"- {acc}" for acc in chart_of_accounts)}
{hist_text}

Remember:
- For expenses (negative amounts), debit the expense account and credit Cash at Bank
- For revenue (positive amounts), debit Cash at Bank and credit the revenue account
- Always ensure debits = credits (balanced entry)
- Set needs_review=true if amount > $5000 or if uncertain
"""
    
    return prompt

