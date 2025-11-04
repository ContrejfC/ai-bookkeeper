#!/usr/bin/env python3
"""
Train Template System from Sample Bank Statements
==================================================

This script:
1. Analyzes real bank statement PDFs in tests/fixtures/pdf/_public_samples/
2. Extracts features (headers, tables, geometry)
3. Identifies which banks they're from
4. Creates or updates YAML templates
5. Stores features (NOT PDFs) for future use

Usage:
    python scripts/train_from_samples.py
    python scripts/train_from_samples.py --verbose
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any
import re

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

# Bank detection patterns
BANK_PATTERNS = {
    'chase': ['chase', 'jpmorgan', 'jp morgan'],
    'wells_fargo': ['wells fargo', 'wellsfargo'],
    'bank_of_america': ['bank of america', 'bankofamerica', 'bofa'],
    'citibank': ['citibank', 'citi', 'citicorp'],
    'goldman_sachs': ['goldman sachs', 'goldman'],
    'pnc': ['pnc bank', 'pnc financial'],
    'morgan_stanley': ['morgan stanley'],
    'us_bank': ['u.s. bank', 'us bank', 'usbank'],
    'truist': ['truist', 'bb&t', 'suntrust'],
    'first_citizens': ['first citizens', 'firstcitizens'],
    'bmo': ['bmo', 'bank of montreal', 'harris bank'],
    'td_bank': ['td bank', 'toronto dominion'],
    'capital_one': ['capital one', 'capitalone'],
    'charles_schwab': ['charles schwab', 'schwab'],
    'mt_bank': ['m&t bank', 'm and t bank'],
    'fifth_third': ['fifth third', '53 bank', '5/3 bank'],
    'huntington': ['huntington bank', 'huntington national'],
    'key_bank': ['keybank', 'key bank', 'keycorp'],
    'citizens_bank': ['citizens bank', 'citizens financial'],
    'american_express': ['american express', 'amex'],
}


def check_dependencies():
    """Check if required dependencies are installed."""
    missing = []
    
    if not HAS_PDFPLUMBER:
        missing.append('pdfplumber')
    if not HAS_YAML:
        missing.append('pyyaml')
    
    if missing:
        print(f"\n❌ Missing dependencies: {', '.join(missing)}")
        print(f"\nInstall with:")
        print(f"  pip install {' '.join(missing)}")
        return False
    
    return True


def detect_bank(text: str) -> str:
    """Detect which bank a statement is from."""
    text_lower = text.lower()
    
    for bank_key, patterns in BANK_PATTERNS.items():
        for pattern in patterns:
            if pattern in text_lower:
                return bank_key
    
    return 'unknown'


def extract_features_from_pdf(pdf_path: Path) -> Dict[str, Any]:
    """Extract features from a PDF."""
    print(f"\n📄 Analyzing: {pdf_path.name}")
    
    features = {
        'filename': pdf_path.name,
        'header_text': '',
        'footer_text': '',
        'table_headers': [],
        'detected_bank': 'unknown',
        'geometry': {},
        'page_count': 0,
        'sample_text': ''
    }
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            features['page_count'] = len(pdf.pages)
            
            if len(pdf.pages) > 0:
                first_page = pdf.pages[0]
                page_height = first_page.height
                page_width = first_page.width
                
                # Extract full text (for bank detection)
                full_text = first_page.extract_text() or ''
                features['sample_text'] = full_text[:2000]  # First 2000 chars
                
                # Detect bank
                features['detected_bank'] = detect_bank(full_text)
                
                # Extract header region (top 20%)
                header_region = first_page.within_bbox((0, 0, page_width, page_height * 0.20))
                features['header_text'] = (header_region.extract_text() or '').strip()
                
                # Extract footer region (bottom 15%)
                footer_region = first_page.within_bbox((0, page_height * 0.85, page_width, page_height))
                features['footer_text'] = (footer_region.extract_text() or '').strip()
                
                # Extract tables
                tables = first_page.extract_tables()
                if tables:
                    for table in tables:
                        if table and len(table) > 0:
                            header_row = table[0]
                            clean_headers = [str(h).strip() if h else '' for h in header_row]
                            if any(clean_headers):
                                features['table_headers'].append(clean_headers)
                
                # Geometry
                features['geometry'] = {
                    'header_band': [0.0, 0.20],
                    'table_band': [0.25, 0.80]
                }
        
        print(f"   ✅ Extracted features")
        print(f"   🏦 Detected bank: {features['detected_bank']}")
        print(f"   📊 Found {len(features['table_headers'])} table(s)")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    return features


def save_features(features: Dict[str, Any], output_dir: Path):
    """Save extracted features to JSON."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filename = Path(features['filename']).stem
    output_path = output_dir / f"{filename}_features.json"
    
    with open(output_path, 'w') as f:
        json.dump(features, f, indent=2)
    
    print(f"   💾 Saved features to: {output_path.name}")


def generate_template_recommendations(all_features: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate recommendations for templates based on extracted features."""
    banks_found = {}
    
    for features in all_features:
        bank = features['detected_bank']
        if bank != 'unknown':
            if bank not in banks_found:
                banks_found[bank] = []
            banks_found[bank].append(features)
    
    recommendations = {
        'banks_detected': list(banks_found.keys()),
        'banks_count': len(banks_found),
        'samples_per_bank': {bank: len(samples) for bank, samples in banks_found.items()},
        'recommendations': []
    }
    
    for bank, samples in banks_found.items():
        # Analyze common patterns
        all_header_text = ' '.join([s['header_text'] for s in samples])
        all_table_headers = []
        for s in samples:
            all_table_headers.extend(s['table_headers'])
        
        rec = {
            'bank': bank,
            'sample_count': len(samples),
            'action': 'create_template' if bank not in ['chase', 'wells_fargo', 'fifth_third', 'bank_of_america', 'us_bank'] else 'update_template',
            'common_keywords': extract_common_keywords(all_header_text),
            'table_header_examples': all_table_headers[:3] if all_table_headers else []
        }
        
        recommendations['recommendations'].append(rec)
    
    return recommendations


def extract_common_keywords(text: str) -> List[str]:
    """Extract common banking keywords from text."""
    keywords = ['statement', 'account', 'balance', 'transaction', 'period', 'summary']
    found = []
    
    text_lower = text.lower()
    for keyword in keywords:
        if keyword in text_lower:
            found.append(keyword)
    
    return found


def main():
    parser = argparse.ArgumentParser(description='Train template system from sample bank statements')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--samples-dir', default='tests/fixtures/pdf/_public_samples', 
                       help='Directory containing sample PDFs')
    parser.add_argument('--output-dir', default='tests/fixtures/pdf/features', 
                       help='Directory to save extracted features')
    
    args = parser.parse_args()
    
    print("="*80)
    print("BANK STATEMENT TEMPLATE TRAINING")
    print("="*80)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Find sample PDFs
    samples_dir = Path(args.samples_dir)
    if not samples_dir.exists():
        print(f"\n❌ Samples directory not found: {samples_dir}")
        sys.exit(1)
    
    pdf_files = list(samples_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"\n❌ No PDF files found in {samples_dir}")
        sys.exit(1)
    
    print(f"\n📁 Found {len(pdf_files)} sample PDF(s)")
    
    # Process each PDF
    all_features = []
    for pdf_path in sorted(pdf_files):
        features = extract_features_from_pdf(pdf_path)
        all_features.append(features)
        
        # Save features
        save_features(features, Path(args.output_dir))
    
    # Generate recommendations
    print(f"\n{'='*80}")
    print("ANALYSIS SUMMARY")
    print(f"{'='*80}")
    
    recommendations = generate_template_recommendations(all_features)
    
    print(f"\n🏦 Banks Detected: {recommendations['banks_count']}")
    for bank in recommendations['banks_detected']:
        count = recommendations['samples_per_bank'][bank]
        print(f"   - {bank}: {count} sample(s)")
    
    print(f"\n📋 Recommendations:")
    for rec in recommendations['recommendations']:
        print(f"\n   🏦 {rec['bank'].upper()}")
        print(f"      Action: {rec['action']}")
        print(f"      Samples: {rec['sample_count']}")
        if rec['common_keywords']:
            print(f"      Keywords: {', '.join(rec['common_keywords'])}")
    
    # Save recommendations
    rec_path = Path(args.output_dir) / "_training_recommendations.json"
    with open(rec_path, 'w') as f:
        json.dump(recommendations, f, indent=2)
    
    print(f"\n💾 Saved recommendations to: {rec_path}")
    
    print(f"\n{'='*80}")
    print("✅ TRAINING COMPLETE")
    print(f"{'='*80}")
    
    print(f"\nNext steps:")
    print(f"  1. Review features in: {args.output_dir}")
    print(f"  2. Review recommendations in: {rec_path}")
    print(f"  3. Create/update templates in: app/ingestion/templates/banks/")
    print(f"  4. Run tests: pytest tests/templates/ -v")
    print(f"\n📚 See: docs/TEMPLATES_README.md for more info")


if __name__ == '__main__':
    main()



