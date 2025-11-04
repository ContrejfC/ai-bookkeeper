"""
CSV Fuzzer - Locale Variant Generator
=====================================

Generates CSV files with different locale conventions to test normalization robustness.

Variants include:
- Delimiters: comma, semicolon, tab, pipe
- Decimal separators: period, comma
- Thousands separators: comma, period, space, apostrophe
- Negative signs: prefix minus, suffix minus, parentheses, CR suffix
- Date formats: MDY, DMY, YMD with various separators
- Encodings: UTF-8, Latin-1, Windows-1252
"""

from app.ingestion.csv_fuzz.fuzz_csv import generate_variants

__all__ = ["generate_variants"]



