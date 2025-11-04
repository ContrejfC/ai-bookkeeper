"""
CSV and XML Feature Extraction
==============================

Extract non-PII layout features from CSV, XML, and text-based financial formats.
Supports: CSV, OFX, QFX, camt.053/054, MT940, BAI2, and generic XML.
"""

import csv
import io
import json
import logging
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

try:
    import chardet
    HAS_CHARDET = True
except ImportError:
    HAS_CHARDET = False

from app.ingestion.utils.pii import redact_pii

logger = logging.getLogger(__name__)

if not HAS_CHARDET:
    logger.warning("chardet not installed. Using UTF-8 encoding detection fallback.")

# ============================================================================
# CSV Feature Extraction
# ============================================================================

def extract_csv_features(file_content: bytes, file_name: str) -> Dict[str, Any]:
    """
    Extract features from CSV files.
    
    Returns:
        {
            "file_name": str,
            "encoding": str,
            "delimiter": str,
            "has_header": bool,
            "column_count": int,
            "row_count": int (sampled),
            "header_tokens": [str],  # PII-redacted
            "column_map_guess": {col_name: type_guess},
            "sample_rows": [row]  # PII-redacted, first 3 rows
        }
    """
    # Detect encoding
    if HAS_CHARDET:
        encoding_info = chardet.detect(file_content)
        encoding = encoding_info.get("encoding", "utf-8")
    else:
        encoding = "utf-8"
    
    try:
        text = file_content.decode(encoding)
    except Exception as e:
        logger.error(f"Failed to decode CSV with {encoding}: {e}")
        text = file_content.decode('utf-8', errors='ignore')
        encoding = "utf-8 (fallback)"
    
    # Detect delimiter
    delimiter = _detect_csv_delimiter(text)
    
    # Parse CSV
    try:
        reader = csv.reader(io.StringIO(text), delimiter=delimiter)
        rows = list(reader)
    except Exception as e:
        logger.error(f"Failed to parse CSV: {e}")
        return {"error": str(e), "file_name": file_name}
    
    if not rows:
        return {"error": "Empty CSV", "file_name": file_name}
    
    # Detect if first row is header
    has_header = _is_header_row(rows[0]) if len(rows) > 1 else True
    
    header_tokens = []
    data_rows = rows
    
    if has_header:
        header_tokens = [redact_pii(token.strip()) for token in rows[0]]
        data_rows = rows[1:]
    else:
        # Generate generic column names
        header_tokens = [f"Column_{i+1}" for i in range(len(rows[0]))]
    
    # Column type guessing
    column_map = _guess_column_types(header_tokens, data_rows[:10])
    
    # Sample rows (PII redacted)
    sample_rows = []
    for row in data_rows[:3]:
        redacted_row = [redact_pii(str(cell)) for cell in row]
        sample_rows.append(redacted_row)
    
    features = {
        "file_name": file_name,
        "format": "csv",
        "encoding": encoding,
        "delimiter": delimiter,
        "has_header": has_header,
        "column_count": len(header_tokens),
        "row_count_sampled": len(data_rows),
        "header_tokens": header_tokens,
        "column_map_guess": column_map,
        "sample_rows": sample_rows,
    }
    
    return features


def _detect_csv_delimiter(text: str) -> str:
    """Detect CSV delimiter by analyzing first few lines."""
    lines = text.split('\n')[:5]
    
    # Count occurrences of common delimiters
    delimiters = {',': 0, '\t': 0, ';': 0, '|': 0}
    
    for line in lines:
        for delim in delimiters:
            delimiters[delim] += line.count(delim)
    
    # Return most common (with preference for comma)
    if delimiters[','] > 0:
        return ','
    return max(delimiters, key=delimiters.get)


def _is_header_row(row: List[str]) -> bool:
    """Heuristic to detect if a row is a header row."""
    # Headers typically have:
    # - No numbers
    # - Descriptive text
    # - Common header keywords
    
    header_keywords = ["date", "description", "amount", "balance", "debit", "credit",
                      "transaction", "reference", "type", "category", "account",
                      "posting", "value", "memo", "payee", "check"]
    
    has_keyword = any(any(kw in cell.lower() for kw in header_keywords) for cell in row)
    has_no_numbers = all(not any(c.isdigit() for c in cell) for cell in row)
    
    return has_keyword or has_no_numbers


def _guess_column_types(headers: List[str], sample_rows: List[List[str]]) -> Dict[str, str]:
    """
    Guess column types based on headers and sample data.
    
    Returns:
        {column_name: guess}
        guess: "date", "amount", "description", "balance", "reference", "unknown"
    """
    column_map = {}
    
    for i, header in enumerate(headers):
        header_lower = header.lower()
        
        # Check header keywords first
        if any(kw in header_lower for kw in ["date", "dt", "posted", "transaction date"]):
            column_map[header] = "date"
        elif any(kw in header_lower for kw in ["amount", "amt", "value"]):
            column_map[header] = "amount"
        elif any(kw in header_lower for kw in ["balance", "bal"]):
            column_map[header] = "balance"
        elif any(kw in header_lower for kw in ["description", "desc", "memo", "payee", "merchant"]):
            column_map[header] = "description"
        elif any(kw in header_lower for kw in ["debit", "withdrawal", "out"]):
            column_map[header] = "debit"
        elif any(kw in header_lower for kw in ["credit", "deposit", "in"]):
            column_map[header] = "credit"
        elif any(kw in header_lower for kw in ["reference", "ref", "id", "transaction id"]):
            column_map[header] = "reference"
        else:
            # Analyze sample data
            sample_values = [row[i] for row in sample_rows if i < len(row)]
            column_map[header] = _guess_type_from_values(sample_values)
    
    return column_map


def _guess_type_from_values(values: List[str]) -> str:
    """Guess column type from sample values."""
    if not values:
        return "unknown"
    
    # Check if mostly dates
    date_patterns = [
        r'\d{1,2}/\d{1,2}/\d{2,4}',
        r'\d{4}-\d{2}-\d{2}',
        r'\d{1,2}-\d{1,2}-\d{2,4}',
    ]
    date_matches = sum(1 for v in values if any(re.match(p, v) for p in date_patterns))
    if date_matches / len(values) > 0.7:
        return "date"
    
    # Check if mostly amounts (numbers with optional currency symbols)
    amount_pattern = r'^[\$£€]?\s*-?\d+[.,]?\d*$'
    amount_matches = sum(1 for v in values if re.match(amount_pattern, v.strip()))
    if amount_matches / len(values) > 0.7:
        return "amount"
    
    # Check if mostly text (descriptions)
    text_matches = sum(1 for v in values if len(v) > 5 and any(c.isalpha() for c in v))
    if text_matches / len(values) > 0.7:
        return "description"
    
    return "unknown"


# ============================================================================
# XML Feature Extraction
# ============================================================================

def extract_xml_features(file_content: bytes, file_name: str) -> Dict[str, Any]:
    """
    Extract features from XML files (OFX, camt.053/054, generic).
    
    Returns:
        {
            "file_name": str,
            "format": str,  # "ofx", "camt.053", "camt.054", "generic_xml"
            "encoding": str,
            "root_tag": str,
            "namespace": str,
            "tag_paths": [str],  # Unique tag paths (redacted)
            "currency": str,
            "date_format_hints": [str],
            "sample_structure": dict  # Simplified tree structure
        }
    """
    try:
        # Try to parse as XML
        tree = ET.ElementTree(ET.fromstring(file_content))
        root = tree.getroot()
    except Exception as e:
        logger.error(f"Failed to parse XML: {e}")
        return {"error": str(e), "file_name": file_name}
    
    # Detect XML format
    xml_format = _detect_xml_format(root)
    
    # Extract namespace
    namespace = root.tag.split('}')[0].strip('{') if '}' in root.tag else ""
    
    # Extract tag paths (for structure understanding)
    tag_paths = _extract_tag_paths(root, max_depth=5)
    
    # Look for currency information
    currency = _find_currency(root)
    
    # Look for date formats
    date_hints = _find_date_formats(root)
    
    # Create simplified structure (first few levels)
    sample_structure = _create_sample_structure(root, max_depth=3)
    
    features = {
        "file_name": file_name,
        "format": xml_format,
        "encoding": "utf-8",  # XML is typically UTF-8
        "root_tag": _strip_namespace(root.tag),
        "namespace": namespace,
        "tag_paths": list(set(tag_paths)),
        "currency": currency,
        "date_format_hints": date_hints,
        "sample_structure": sample_structure,
    }
    
    return features


def _detect_xml_format(root: ET.Element) -> str:
    """Detect specific XML format."""
    root_tag = _strip_namespace(root.tag).lower()
    
    if root_tag == "ofx":
        return "ofx"
    elif root_tag == "document" or "camt.053" in str(root.attrib):
        return "camt.053"
    elif root_tag == "document" or "camt.054" in str(root.attrib):
        return "camt.054"
    else:
        return "generic_xml"


def _strip_namespace(tag: str) -> str:
    """Remove XML namespace from tag."""
    return tag.split('}')[-1] if '}' in tag else tag


def _extract_tag_paths(element: ET.Element, prefix: str = "", max_depth: int = 5) -> List[str]:
    """Extract all unique tag paths in the XML tree."""
    if max_depth <= 0:
        return []
    
    paths = []
    tag = _strip_namespace(element.tag)
    current_path = f"{prefix}/{tag}" if prefix else tag
    paths.append(current_path)
    
    for child in element:
        paths.extend(_extract_tag_paths(child, current_path, max_depth - 1))
    
    return paths


def _find_currency(element: ET.Element) -> str:
    """Search for currency information in XML."""
    # Common currency tag names
    currency_tags = ["Ccy", "Currency", "CCY", "CurrencyCode"]
    
    for tag in currency_tags:
        for elem in element.iter():
            if _strip_namespace(elem.tag) == tag and elem.text:
                return elem.text.strip()
    
    return "unknown"


def _find_date_formats(element: ET.Element) -> List[str]:
    """Find date format patterns in XML."""
    date_patterns = []
    date_tags = ["Date", "Dt", "DateTime", "CreDtTm", "BookgDt"]
    
    for tag in date_tags:
        for elem in element.iter():
            if _strip_namespace(elem.tag) == tag and elem.text:
                date_value = elem.text.strip()
                # Detect format
                if re.match(r'\d{4}-\d{2}-\d{2}', date_value):
                    date_patterns.append("YYYY-MM-DD")
                elif re.match(r'\d{8}', date_value):
                    date_patterns.append("YYYYMMDD")
                elif re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', date_value):
                    date_patterns.append("ISO8601")
                break
    
    return list(set(date_patterns))


def _create_sample_structure(element: ET.Element, max_depth: int = 3, depth: int = 0) -> Dict:
    """Create a simplified structure representation."""
    if depth >= max_depth:
        return {"tag": _strip_namespace(element.tag), "truncated": True}
    
    structure = {
        "tag": _strip_namespace(element.tag),
        "has_text": bool(element.text and element.text.strip()),
        "attributes": list(element.attrib.keys()),
        "children": []
    }
    
    # Sample first few children of each type
    child_counts = {}
    for child in element:
        child_tag = _strip_namespace(child.tag)
        if child_tag not in child_counts:
            child_counts[child_tag] = 0
            structure["children"].append(_create_sample_structure(child, max_depth, depth + 1))
        child_counts[child_tag] += 1
    
    structure["child_counts"] = child_counts
    
    return structure


# ============================================================================
# Text Format Feature Extraction (BAI2, MT940)
# ============================================================================

def extract_txt_features(file_content: bytes, file_name: str) -> Dict[str, Any]:
    """
    Extract features from text-based financial formats (BAI2, MT940).
    
    Returns:
        {
            "file_name": str,
            "format": str,  # "bai2", "mt940", "generic_txt"
            "encoding": str,
            "line_count": int,
            "record_types": [str],  # For BAI2
            "tag_types": [str],  # For MT940
            "structure_summary": dict
        }
    """
    # Detect encoding
    if HAS_CHARDET:
        encoding_info = chardet.detect(file_content)
        encoding = encoding_info.get("encoding", "utf-8")
    else:
        encoding = "utf-8"
    
    try:
        text = file_content.decode(encoding)
    except Exception:
        text = file_content.decode('utf-8', errors='ignore')
        encoding = "utf-8 (fallback)"
    
    lines = text.split('\n')
    
    # Detect format
    txt_format = _detect_txt_format(lines)
    
    if txt_format == "bai2":
        features = _extract_bai2_features(lines, file_name, encoding)
    elif txt_format == "mt940":
        features = _extract_mt940_features(lines, file_name, encoding)
    else:
        features = {
            "file_name": file_name,
            "format": "generic_txt",
            "encoding": encoding,
            "line_count": len(lines),
            "first_lines_sample": [redact_pii(line) for line in lines[:5]],
        }
    
    return features


def _detect_txt_format(lines: List[str]) -> str:
    """Detect if text is BAI2, MT940, or generic."""
    if not lines:
        return "generic_txt"
    
    first_line = lines[0].strip()
    
    # BAI2 starts with "01," record
    if first_line.startswith("01,"):
        return "bai2"
    
    # MT940 has ":XX:" tags
    if any(re.match(r':\d{2}:', line) for line in lines[:10]):
        return "mt940"
    
    return "generic_txt"


def _extract_bai2_features(lines: List[str], file_name: str, encoding: str) -> Dict[str, Any]:
    """Extract features from BAI2 format."""
    record_types = set()
    
    for line in lines:
        # BAI2 records start with a two-digit code
        match = re.match(r'^(\d{2}),', line)
        if match:
            record_types.add(match.group(1))
    
    return {
        "file_name": file_name,
        "format": "bai2",
        "encoding": encoding,
        "line_count": len(lines),
        "record_types": sorted(list(record_types)),
        "structure_summary": {
            "01_file_header": "01" in record_types,
            "02_group_header": "02" in record_types,
            "03_account_identifier": "03" in record_types,
            "16_transaction_detail": "16" in record_types,
            "49_account_trailer": "49" in record_types,
            "98_group_trailer": "98" in record_types,
            "99_file_trailer": "99" in record_types,
        }
    }


def _extract_mt940_features(lines: List[str], file_name: str, encoding: str) -> Dict[str, Any]:
    """Extract features from MT940 format."""
    tag_types = set()
    
    for line in lines:
        # MT940 tags are :XX:
        match = re.match(r':(\d{2,3}):', line)
        if match:
            tag_types.add(match.group(1))
    
    return {
        "file_name": file_name,
        "format": "mt940",
        "encoding": encoding,
        "line_count": len(lines),
        "tag_types": sorted(list(tag_types)),
        "structure_summary": {
            "20_transaction_reference": "20" in tag_types,
            "25_account_number": "25" in tag_types,
            "28_statement_number": "28" in tag_types,
            "60_opening_balance": "60" in tag_types or "60F" in tag_types,
            "61_statement_line": "61" in tag_types,
            "62_closing_balance": "62" in tag_types or "62F" in tag_types,
            "86_information": "86" in tag_types,
        }
    }


# ============================================================================
# Main Entry Point
# ============================================================================

def extract_features(file_content: bytes, file_type: str, file_name: str) -> Dict[str, Any]:
    """
    Main entry point for feature extraction.
    
    Args:
        file_content: Raw file bytes
        file_type: "csv", "xml", or "txt"
        file_name: Original file name
        
    Returns:
        Feature dictionary (PII-redacted)
    """
    try:
        if file_type == "csv":
            return extract_csv_features(file_content, file_name)
        elif file_type == "xml":
            return extract_xml_features(file_content, file_name)
        elif file_type == "txt":
            return extract_txt_features(file_content, file_name)
        else:
            return {"error": f"Unsupported file type: {file_type}", "file_name": file_name}
    except Exception as e:
        logger.error(f"Feature extraction failed for {file_name}: {e}")
        return {"error": str(e), "file_name": file_name, "file_type": file_type}


# Example usage
if __name__ == "__main__":
    # Test CSV
    csv_content = b"Date,Description,Amount,Balance\n01/01/2023,Purchase,-50.00,1000.00\n01/02/2023,Deposit,100.00,1100.00"
    csv_features = extract_csv_features(csv_content, "test.csv")
    print("CSV Features:")
    print(json.dumps(csv_features, indent=2))
    
    # Test XML (OFX-like)
    xml_content = b"""<?xml version="1.0"?>
    <OFX>
        <BANKMSGSRSV1>
            <STMTTRNRS>
                <STMTRS>
                    <CURDEF>USD</CURDEF>
                    <BANKTRANLIST>
                        <DTSTART>20230101</DTSTART>
                        <DTEND>20230131</DTEND>
                    </BANKTRANLIST>
                </STMTRS>
            </STMTTRNRS>
        </BANKMSGSRSV1>
    </OFX>"""
    xml_features = extract_xml_features(xml_content, "test.ofx")
    print("\nXML Features:")
    print(json.dumps(xml_features, indent=2))
    
    # Test BAI2
    bai2_content = b"01,ABC Bank,123456,230101,1200,USD/\n03,123456789,USD,010,100000/\n16,195,5000,V,230101,,,DEPOSIT/\n49,200000,2/\n99,200000,1,4/"
    bai2_features = extract_txt_features(bai2_content, "test.bai")
    print("\nBAI2 Features:")
    print(json.dumps(bai2_features, indent=2))

