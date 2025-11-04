"""
CSV Fuzzer - Generate Locale Variants
=====================================

Generates multiple CSV files with different locale conventions from a template.

Usage:
    python -m app.ingestion.csv_fuzz.fuzz_csv --in template.csv --out output_dir --variants 12
"""

import argparse
import csv
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple


# Fuzzing configurations
DELIMITERS = [',', ';', '\t', '|']
DECIMAL_SEPS = ['.', ',']
THOUSAND_SEPS = [',', '.', ' ', "'", '']
NEGATIVE_FORMATS = [
    lambda x: f"-{x}",      # -123.45
    lambda x: f"{x}-",      # 123.45-
    lambda x: f"({x})",     # (123.45)
    lambda x: f"{x} CR",    # 123.45 CR
]
DATE_FORMATS = [
    ('MM/DD/YYYY', r'(\d{2})/(\d{2})/(\d{4})'),  # US format
    ('DD/MM/YYYY', r'(\d{2})/(\d{2})/(\d{4})'),  # European format
    ('YYYY-MM-DD', r'(\d{4})-(\d{2})-(\d{2})'),  # ISO format
    ('DD.MM.YYYY', r'(\d{2})\.(\d{2})\.(\d{4})'), # German format
]
ENCODINGS = ['utf-8', 'latin-1', 'windows-1252']


def generate_variants(input_file: Path, output_dir: Path, num_variants: int = 12) -> List[Path]:
    """
    Generate multiple CSV variants from a template file.
    
    Args:
        input_file: Path to template CSV
        output_dir: Directory to write variants
        num_variants: Number of variants to generate
        
    Returns:
        List of paths to generated variant files
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Read template
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        rows = list(reader)
    
    # Generate variant configurations
    configs = _generate_configs(num_variants)
    
    generated_files = []
    
    for i, config in enumerate(configs):
        variant_name = f"{input_file.stem}_variant_{i+1:02d}.csv"
        variant_path = output_dir / variant_name
        
        _write_variant(variant_path, headers, rows, config)
        generated_files.append(variant_path)
        
        print(f"Generated: {variant_path.name}")
        print(f"  Delimiter: {repr(config['delimiter'])}")
        print(f"  Decimal: {config['decimal_sep']}, Thousands: {config['thousand_sep']}")
        print(f"  Negative: {config['negative_style']}, Date: {config['date_format'][0]}")
        print(f"  Encoding: {config['encoding']}")
        print()
    
    return generated_files


def _generate_configs(num_variants: int) -> List[Dict[str, Any]]:
    """Generate diverse fuzzing configurations."""
    configs = []
    
    # Predefined interesting combinations
    base_configs = [
        # Standard US
        {'delimiter': ',', 'decimal_sep': '.', 'thousand_sep': ',', 
         'negative_style': 0, 'date_format': DATE_FORMATS[0], 'encoding': 'utf-8'},
        
        # European (semicolon, comma decimal)
        {'delimiter': ';', 'decimal_sep': ',', 'thousand_sep': '.', 
         'negative_style': 0, 'date_format': DATE_FORMATS[1], 'encoding': 'utf-8'},
        
        # Tab-delimited
        {'delimiter': '\t', 'decimal_sep': '.', 'thousand_sep': ',', 
         'negative_style': 0, 'date_format': DATE_FORMATS[0], 'encoding': 'utf-8'},
        
        # Parentheses for negative
        {'delimiter': ',', 'decimal_sep': '.', 'thousand_sep': ',', 
         'negative_style': 2, 'date_format': DATE_FORMATS[0], 'encoding': 'utf-8'},
        
        # CR suffix for credit
        {'delimiter': ',', 'decimal_sep': '.', 'thousand_sep': '', 
         'negative_style': 3, 'date_format': DATE_FORMATS[0], 'encoding': 'utf-8'},
        
        # ISO date format
        {'delimiter': ',', 'decimal_sep': '.', 'thousand_sep': ',', 
         'negative_style': 0, 'date_format': DATE_FORMATS[2], 'encoding': 'utf-8'},
        
        # German format
        {'delimiter': ';', 'decimal_sep': ',', 'thousand_sep': '.', 
         'negative_style': 0, 'date_format': DATE_FORMATS[3], 'encoding': 'latin-1'},
        
        # Pipe delimiter
        {'delimiter': '|', 'decimal_sep': '.', 'thousand_sep': ' ', 
         'negative_style': 0, 'date_format': DATE_FORMATS[0], 'encoding': 'utf-8'},
        
        # Apostrophe thousands
        {'delimiter': ',', 'decimal_sep': '.', 'thousand_sep': "'", 
         'negative_style': 0, 'date_format': DATE_FORMATS[0], 'encoding': 'utf-8'},
        
        # Suffix minus
        {'delimiter': ',', 'decimal_sep': '.', 'thousand_sep': ',', 
         'negative_style': 1, 'date_format': DATE_FORMATS[0], 'encoding': 'utf-8'},
        
        # Space thousands, comma decimal
        {'delimiter': ';', 'decimal_sep': ',', 'thousand_sep': ' ', 
         'negative_style': 0, 'date_format': DATE_FORMATS[1], 'encoding': 'utf-8'},
        
        # Windows encoding
        {'delimiter': ',', 'decimal_sep': '.', 'thousand_sep': ',', 
         'negative_style': 0, 'date_format': DATE_FORMATS[0], 'encoding': 'windows-1252'},
    ]
    
    # Return requested number of variants
    return base_configs[:num_variants]


def _write_variant(output_path: Path, headers: List[str], rows: List[Dict], config: Dict[str, Any]):
    """Write a CSV variant with the given configuration."""
    delimiter = config['delimiter']
    decimal_sep = config['decimal_sep']
    thousand_sep = config['thousand_sep']
    negative_formatter = NEGATIVE_FORMATS[config['negative_style']]
    date_format = config['date_format']
    encoding = config['encoding']
    
    # Transform rows
    transformed_rows = []
    for row in rows:
        transformed_row = {}
        for key, value in row.items():
            # Transform amounts
            if _is_amount_field(key):
                value = _transform_amount(value, decimal_sep, thousand_sep, negative_formatter)
            
            # Transform dates
            elif _is_date_field(key):
                value = _transform_date(value, date_format)
            
            transformed_row[key] = value
        
        transformed_rows.append(transformed_row)
    
    # Write file
    with open(output_path, 'w', encoding=encoding, newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers, delimiter=delimiter)
        writer.writeheader()
        writer.writerows(transformed_rows)


def _is_amount_field(field_name: str) -> bool:
    """Check if field is an amount/number field."""
    amount_keywords = ['amount', 'debit', 'credit', 'balance', 'total', 'price']
    field_lower = field_name.lower()
    return any(kw in field_lower for kw in amount_keywords)


def _is_date_field(field_name: str) -> bool:
    """Check if field is a date field."""
    date_keywords = ['date', 'dt', 'posted', 'transaction']
    field_lower = field_name.lower()
    return any(kw in field_lower for kw in date_keywords)


def _transform_amount(value: str, decimal_sep: str, thousand_sep: str, negative_formatter) -> str:
    """Transform amount with locale conventions."""
    if not value or value.strip() == '':
        return value
    
    # Parse original amount
    value_clean = value.strip().replace(',', '')
    
    try:
        amount = float(value_clean)
    except ValueError:
        return value  # Return as-is if not a number
    
    # Handle negative
    is_negative = amount < 0
    abs_amount = abs(amount)
    
    # Split into integer and decimal parts
    int_part = int(abs_amount)
    dec_part = abs_amount - int_part
    
    # Format integer part with thousands separator
    int_str = f"{int_part:,}".replace(',', thousand_sep) if thousand_sep else str(int_part)
    
    # Format decimal part
    dec_str = f"{dec_part:.2f}"[2:]  # Get decimal digits only
    
    # Combine
    if decimal_sep == '.':
        formatted = f"{int_str}.{dec_str}"
    else:
        formatted = f"{int_str}{decimal_sep}{dec_str}"
    
    # Apply negative format
    if is_negative:
        formatted = negative_formatter(formatted)
    
    return formatted


def _transform_date(value: str, date_format: Tuple[str, str]) -> str:
    """Transform date to specified format."""
    if not value or value.strip() == '':
        return value
    
    target_format, pattern = date_format
    
    # Try to parse common formats
    for fmt in ['%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d', '%d.%m.%Y']:
        try:
            dt = datetime.strptime(value.strip(), fmt)
            
            # Convert to target format
            if target_format == 'MM/DD/YYYY':
                return dt.strftime('%m/%d/%Y')
            elif target_format == 'DD/MM/YYYY':
                return dt.strftime('%d/%m/%Y')
            elif target_format == 'YYYY-MM-DD':
                return dt.strftime('%Y-%m-%d')
            elif target_format == 'DD.MM.YYYY':
                return dt.strftime('%d.%m.%Y')
            
        except ValueError:
            continue
    
    return value  # Return as-is if parsing fails


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Generate CSV locale variants for testing normalization',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate 12 variants
  python -m app.ingestion.csv_fuzz.fuzz_csv --in template.csv --out variants/
  
  # Generate 6 variants
  python -m app.ingestion.csv_fuzz.fuzz_csv --in qbo_4col.csv --out test_data/ --variants 6
        """
    )
    
    parser.add_argument('--in', dest='input_file', required=True, type=Path,
                        help='Input CSV template file')
    parser.add_argument('--out', dest='output_dir', required=True, type=Path,
                        help='Output directory for variants')
    parser.add_argument('--variants', type=int, default=12,
                        help='Number of variants to generate (default: 12)')
    
    args = parser.parse_args()
    
    print(f"Generating {args.variants} CSV variants...")
    print(f"Input: {args.input_file}")
    print(f"Output: {args.output_dir}")
    print()
    
    generated = generate_variants(args.input_file, args.output_dir, args.variants)
    
    print(f"\n✅ Generated {len(generated)} variant files in {args.output_dir}")


if __name__ == '__main__':
    main()



