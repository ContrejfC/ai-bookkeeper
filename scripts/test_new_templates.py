#!/usr/bin/env python3
"""
Test New Bank Templates
========================

Quick script to verify the 4 new bank templates work with your samples.
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.ingestion.templates.registry import get_default_registry

def test_templates():
    """Test that new templates can match your sample features."""
    
    print("="*80)
    print("TESTING NEW BANK TEMPLATES")
    print("="*80)
    
    # Load registry
    registry = get_default_registry()
    print(f"\n✅ Loaded {len(registry)} templates")
    
    # List all templates
    print(f"\n📋 Available Templates:")
    for template in registry.templates:
        print(f"   - {template.name} ({template.bank_name})")
    
    # Test features directory
    features_dir = project_root / "tests/fixtures/pdf/features"
    
    if not features_dir.exists():
        print(f"\n❌ Features directory not found: {features_dir}")
        return
    
    feature_files = [
        "account-analysis-guide_features.json",  # Truist
        "document_features.json",                 # Charles Schwab
        "sample-estatement_features.json",        # Capital One
        "single_accounts_redesign_features.json", # KeyBank
    ]
    
    print(f"\n{'='*80}")
    print("TESTING TEMPLATE MATCHES")
    print(f"{'='*80}")
    
    for feature_file in feature_files:
        feature_path = features_dir / feature_file
        
        if not feature_path.exists():
            print(f"\n❌ Feature file not found: {feature_file}")
            continue
        
        with open(feature_path, 'r') as f:
            features = json.load(f)
        
        print(f"\n📄 Testing: {feature_file}")
        print(f"   Expected Bank: {features.get('detected_bank', 'unknown')}")
        
        # Get best match
        best_match = registry.get_best_match(features)
        
        if best_match:
            print(f"   ✅ Matched: {best_match.template.bank_name}")
            print(f"   Score: {best_match.score:.3f} (threshold: {best_match.template.accept_threshold:.3f})")
            print(f"   Component Scores:")
            for component, score in best_match.component_scores.items():
                print(f"      - {component}: {score:.3f}")
            
            if best_match.matched_tokens.get('headers'):
                print(f"   Matched Header Tokens: {', '.join(best_match.matched_tokens['headers'][:3])}")
        else:
            print(f"   ❌ No match found (no template exceeded threshold)")
            
            # Show top 3 matches
            all_matches = registry.match_pdf(features)
            print(f"   Top 3 scores:")
            for i, match in enumerate(all_matches[:3], 1):
                print(f"      {i}. {match.template.bank_name}: {match.score:.3f}")
    
    print(f"\n{'='*80}")
    print("✅ TESTING COMPLETE")
    print(f"{'='*80}")

if __name__ == '__main__':
    test_templates()



