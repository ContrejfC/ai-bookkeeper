"""
Open Data Cleaner - Normalize financial datasets from various sources.

Handles:
- Column name standardization
- Date format parsing
- Amount normalization
- Vendor/counterparty extraction
- MCC code mapping
- Balance integrity validation
"""
import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, date
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)

# Standard column mappings
COLUMN_MAPPINGS = {
    'date': ['date', 'transaction_date', 'posting_date', 'trans_date', 'txn_date', 'Date', 'DATE'],
    'amount': ['amount', 'Amount', 'AMOUNT', 'value', 'transaction_amount', 'txn_amount'],
    'description': ['description', 'Description', 'memo', 'narration', 'details', 'particulars'],
    'counterparty': ['counterparty', 'vendor', 'merchant', 'payee', 'customer', 'party_name'],
    'account': ['account', 'account_name', 'account_code', 'ledger_account', 'gl_account'],
    'currency': ['currency', 'Currency', 'CCY'],
    'debit': ['debit', 'Debit', 'DEBIT', 'dr'],
    'credit': ['credit', 'Credit', 'CREDIT', 'cr']
}

# Merchant Category Codes (MCC) - Sample mapping
MCC_TO_ACCOUNT = {
    # Revenue
    '5411': '8000 Sales Revenue',  # Grocery stores
    '5812': '8000 Sales Revenue',  # Eating places, restaurants
    '5999': '8000 Sales Revenue',  # Miscellaneous retail
    
    # Office & Supplies
    '5943': '6100 Office Supplies',  # Stationery stores
    '5111': '6100 Office Supplies',  # Office supplies
    
    # Software & Tech
    '5734': '6300 Software Subscriptions',  # Computer software
    '7372': '6300 Software Subscriptions',  # Computer programming
    '4816': '6300 Software Subscriptions',  # Computer network services
    
    # Advertising
    '7311': '7000 Advertising',  # Advertising services
    '7333': '7000 Advertising',  # Commercial photography
    
    # Transportation
    '4111': '6500 Travel & Transport',  # Local/suburban commuter transport
    '4121': '6500 Travel & Transport',  # Taxicabs/limousines
    '5541': '6500 Travel & Transport',  # Service stations
    
    # Utilities
    '4900': '6200 Utilities',  # Utilities - electric, gas, water
    '4814': '6300 Software Subscriptions',  # Telecommunication services
    
    # Payroll
    '8999': '6400 Payroll Expenses',  # Professional services
}

# Vendor name patterns for categorization
VENDOR_PATTERNS = {
    r'(?i)(aws|amazon web services|digitalocean|azure|google cloud)': '6300 Software Subscriptions',
    r'(?i)(github|gitlab|jetbrains|microsoft 365|office 365)': '6300 Software Subscriptions',
    r'(?i)(stripe|square|paypal|venmo).*payment': '8000 Sales Revenue',
    r'(?i)(google ads|facebook ads|linkedin ads|twitter ads)': '7000 Advertising',
    r'(?i)(fedex|ups|usps|dhl)': '6600 Shipping & Freight',
    r'(?i)(uber|lyft|taxi|rental car)': '6500 Travel & Transport',
    r'(?i)(electric|gas company|water|utility)': '6200 Utilities',
    r'(?i)(adp|paychex|gusto|payroll)': '6400 Payroll Expenses',
    r'(?i)(office depot|staples|amazon).*supplies': '6100 Office Supplies',
}


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize column names to AI Bookkeeper schema.
    
    Args:
        df: Input dataframe with varying column names
        
    Returns:
        DataFrame with standardized column names
    """
    logger.info(f"Standardizing columns from: {list(df.columns)}")
    
    # Create mapping from actual columns to standard names
    rename_map = {}
    
    for standard_name, variants in COLUMN_MAPPINGS.items():
        for col in df.columns:
            if col in variants:
                rename_map[col] = standard_name
                break
    
    df_renamed = df.rename(columns=rename_map)
    
    # Ensure required columns exist
    required = ['date', 'amount', 'description']
    missing = [col for col in required if col not in df_renamed.columns]
    
    if missing:
        logger.warning(f"Missing required columns: {missing}")
        # Try to infer from available columns
        if 'date' not in df_renamed.columns and len(df_renamed.columns) > 0:
            # First column might be date
            potential_date_col = df_renamed.columns[0]
            if df_renamed[potential_date_col].dtype == 'object':
                df_renamed['date'] = potential_date_col
    
    logger.info(f"Standardized to: {list(df_renamed.columns)}")
    return df_renamed


def parse_dates(df: pd.DataFrame, date_column: str = 'date') -> pd.DataFrame:
    """
    Parse dates from various formats to YYYY-MM-DD.
    
    Args:
        df: Input dataframe
        date_column: Name of date column
        
    Returns:
        DataFrame with parsed dates
    """
    if date_column not in df.columns:
        logger.warning(f"Date column '{date_column}' not found")
        return df
    
    logger.info(f"Parsing dates from column: {date_column}")
    
    # Try pandas automatic parsing
    try:
        df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
        
        # Count how many failed
        failed = df[date_column].isna().sum()
        if failed > 0:
            logger.warning(f"Failed to parse {failed} dates")
        
        # Convert to string format YYYY-MM-DD
        df[date_column] = df[date_column].dt.strftime('%Y-%m-%d')
        
    except Exception as e:
        logger.error(f"Error parsing dates: {e}")
    
    return df


def normalize_amounts(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize amount columns (handle debit/credit, signed amounts).
    
    Args:
        df: Input dataframe
        
    Returns:
        DataFrame with normalized 'amount' column
    """
    logger.info("Normalizing amounts")
    
    # If we have separate debit/credit columns
    if 'debit' in df.columns and 'credit' in df.columns:
        # Convert to numeric
        df['debit'] = pd.to_numeric(df['debit'], errors='coerce').fillna(0)
        df['credit'] = pd.to_numeric(df['credit'], errors='coerce').fillna(0)
        
        # Create signed amount: credit is positive (revenue/income), debit is negative (expense)
        df['amount'] = df['credit'] - df['debit']
        
    elif 'amount' in df.columns:
        # Ensure numeric
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        
        # Check if we have a separate sign column
        if 'type' in df.columns or 'transaction_type' in df.columns:
            type_col = 'type' if 'type' in df.columns else 'transaction_type'
            # If type is 'debit' or 'expense', make negative
            df.loc[df[type_col].str.lower().str.contains('debit|expense|payment', na=False), 'amount'] *= -1
    
    # Remove any NaN amounts
    before_count = len(df)
    df = df.dropna(subset=['amount'])
    after_count = len(df)
    
    if before_count != after_count:
        logger.warning(f"Dropped {before_count - after_count} rows with invalid amounts")
    
    return df


def extract_counterparty(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract counterparty/vendor from description if not present.
    
    Args:
        df: Input dataframe
        
    Returns:
        DataFrame with 'counterparty' column
    """
    if 'counterparty' not in df.columns:
        logger.info("Extracting counterparty from description")
        
        if 'description' in df.columns:
            # Take first 50 chars as counterparty, or extract up to first special char
            df['counterparty'] = df['description'].str.extract(r'^([^-#*]+)')[0]
            df['counterparty'] = df['counterparty'].str.strip()
            
            # Limit length
            df['counterparty'] = df['counterparty'].str[:50]
        else:
            df['counterparty'] = 'Unknown'
    
    return df


def map_vendor_to_account(row: pd.Series, use_mcc: bool = True) -> str:
    """
    Map vendor/description to account using patterns and MCC codes.
    
    Args:
        row: DataFrame row with 'description', 'counterparty', optionally 'mcc'
        use_mcc: Whether to use MCC code mapping
        
    Returns:
        Account code
    """
    # Try MCC code first if available
    if use_mcc and 'mcc' in row and pd.notna(row['mcc']):
        mcc = str(row['mcc'])
        if mcc in MCC_TO_ACCOUNT:
            return MCC_TO_ACCOUNT[mcc]
    
    # Try vendor patterns
    text_to_check = f"{row.get('description', '')} {row.get('counterparty', '')}"
    
    for pattern, account in VENDOR_PATTERNS.items():
        if re.search(pattern, text_to_check):
            return account
    
    # Default based on amount sign
    if 'amount' in row:
        return '8000 Sales Revenue' if row['amount'] > 0 else '6100 Office Supplies'
    
    return '6100 Office Supplies'  # Default


def validate_balance_integrity(df: pd.DataFrame) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate that transactions are balanced (total debits = total credits).
    
    Args:
        df: DataFrame with 'amount' column
        
    Returns:
        Tuple of (is_balanced, metrics_dict)
    """
    if 'amount' not in df.columns:
        return False, {'error': 'No amount column'}
    
    total = df['amount'].sum()
    total_positive = df[df['amount'] > 0]['amount'].sum()
    total_negative = df[df['amount'] < 0]['amount'].abs().sum()
    
    metrics = {
        'total': float(total),
        'total_credits': float(total_positive),
        'total_debits': float(total_negative),
        'balance_diff': float(abs(total_positive - total_negative)),
        'is_balanced': abs(total_positive - total_negative) < 0.01  # Allow 1 cent tolerance
    }
    
    logger.info(f"Balance check: Credits={total_positive:.2f}, Debits={total_negative:.2f}, Diff={metrics['balance_diff']:.2f}")
    
    return metrics['is_balanced'], metrics


def clean_open_dataset(
    df: pd.DataFrame,
    source_name: str,
    add_metadata: bool = True
) -> pd.DataFrame:
    """
    Main cleaning pipeline for open datasets.
    
    Args:
        df: Input dataframe
        source_name: Name of data source (for metadata)
        add_metadata: Whether to add source metadata columns
        
    Returns:
        Cleaned and normalized DataFrame
    """
    logger.info(f"Cleaning dataset from {source_name}: {len(df)} rows")
    
    # Step 1: Standardize columns
    df = standardize_columns(df)
    
    # Step 2: Parse dates
    df = parse_dates(df)
    
    # Step 3: Normalize amounts
    df = normalize_amounts(df)
    
    # Step 4: Extract counterparty
    df = extract_counterparty(df)
    
    # Step 5: Add currency if missing
    if 'currency' not in df.columns:
        df['currency'] = 'USD'
    
    # Step 6: Map to accounts
    if 'account' not in df.columns:
        logger.info("Mapping vendors to accounts")
        df['account'] = df.apply(map_vendor_to_account, axis=1)
    
    # Step 7: Add metadata
    if add_metadata:
        df['source_type'] = 'open_data'
        df['source_name'] = source_name
        df['confidence_source'] = 'synthetic'
        df['imported_at'] = datetime.now().isoformat()
    
    # Step 8: Validate
    is_balanced, metrics = validate_balance_integrity(df)
    logger.info(f"Dataset balance: {'✅ Balanced' if is_balanced else '⚠️ Unbalanced'}")
    
    # Step 9: Drop any remaining NaN in required fields
    required_fields = ['date', 'amount', 'description']
    df = df.dropna(subset=required_fields)
    
    logger.info(f"Cleaned dataset: {len(df)} rows remaining")
    
    return df


def split_train_test(
    df: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split dataset into train and test sets.
    
    Args:
        df: Input dataframe
        test_size: Fraction for test set
        random_state: Random seed
        
    Returns:
        Tuple of (train_df, test_df)
    """
    from sklearn.model_selection import train_test_split
    
    train_df, test_df = train_test_split(
        df,
        test_size=test_size,
        random_state=random_state,
        stratify=df['account'] if 'account' in df.columns else None
    )
    
    logger.info(f"Split: {len(train_df)} train, {len(test_df)} test")
    
    return train_df, test_df
