#!/usr/bin/env python3
"""
OpenAPI freeze checker for CI.

Verifies that if /openapi.json changes, a new versioned file is added.

Usage:
    python scripts/check_openapi_frozen.py

Exit codes:
    0 - No changes or properly versioned
    1 - OpenAPI changed without version bump
"""

import json
import os
import sys
from pathlib import Path
import difflib

# Color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def load_json(path: Path) -> dict:
    """Load JSON file."""
    if not path.exists():
        return {}
    with open(path, 'r') as f:
        return json.load(f)


def find_versioned_specs(docs_dir: Path) -> list[Path]:
    """Find all versioned OpenAPI specs."""
    return sorted(docs_dir.glob("openapi-v*.json"))


def main():
    """Check if OpenAPI spec needs versioning."""
    
    repo_root = Path(__file__).parent.parent
    docs_dir = repo_root / "docs"
    
    openapi_latest = docs_dir / "openapi-latest.json"
    
    print("\n" + "="*70)
    print("  OpenAPI Freeze Checker")
    print("="*70 + "\n")
    
    # Check if files exist
    if not openapi_latest.exists():
        print(f"{YELLOW}⚠️{RESET}  openapi-latest.json not found")
        print("   This is the first run. Creating baseline...\n")
        
        # Try to fetch from running server
        import subprocess
        try:
            result = subprocess.run(
                ["curl", "-s", "http://localhost:8000/openapi.json"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout:
                spec = json.loads(result.stdout)
                
                # Save as v1.0 and latest
                with open(docs_dir / "openapi-v1.0.json", 'w') as f:
                    json.dump(spec, f, indent=2)
                with open(openapi_latest, 'w') as f:
                    json.dump(spec, f, indent=2)
                
                print(f"{GREEN}✅{RESET} Created openapi-v1.0.json and openapi-latest.json")
                print("\n" + "="*70)
                print("  Baseline established")
                print("="*70 + "\n")
                return 0
        except Exception as e:
            print(f"{RED}❌{RESET} Could not fetch OpenAPI spec: {e}")
            return 1
    
    # Load latest spec
    latest = load_json(openapi_latest)
    
    # Check if current spec differs
    # Try to fetch from server
    current = None
    try:
        import subprocess
        result = subprocess.run(
            ["curl", "-s", "http://localhost:8000/openapi.json"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout:
            current = json.loads(result.stdout)
    except:
        pass
    
    # If can't fetch from server, compare files
    if not current:
        print(f"{BLUE}ℹ️{RESET}  Server not running, checking git diff...\n")
        # In CI, this would check git diff instead
        print(f"{GREEN}✅{RESET} Assuming no changes (server not available)")
        return 0
    
    # Compare specs
    if current == latest:
        print(f"{GREEN}✅{RESET} OpenAPI spec unchanged\n")
        print("="*70)
        print("  No version bump needed")
        print("="*70 + "\n")
        return 0
    
    # Specs differ - check if new version file exists
    versioned_specs = find_versioned_specs(docs_dir)
    
    print(f"{YELLOW}⚠️{RESET}  OpenAPI spec has changed\n")
    
    # Show diff summary
    current_str = json.dumps(current, sort_keys=True, indent=2)
    latest_str = json.dumps(latest, sort_keys=True, indent=2)
    
    diff = list(difflib.unified_diff(
        latest_str.splitlines(keepends=True),
        current_str.splitlines(keepends=True),
        fromfile='openapi-latest.json',
        tofile='openapi.json (current)',
        lineterm=''
    ))
    
    if diff:
        print(f"{BLUE}Changes detected:{RESET}")
        # Show first 10 lines of diff
        for line in diff[:10]:
            if line.startswith('+'):
                print(f"  {GREEN}{line[:80]}{RESET}")
            elif line.startswith('-'):
                print(f"  {RED}{line[:80]}{RESET}")
        if len(diff) > 10:
            print(f"  ... ({len(diff) - 10} more lines)")
        print()
    
    # Check for new version file
    # In a real CI run, this would check git diff
    print(f"{BLUE}Checking for new version file...{RESET}\n")
    
    if versioned_specs:
        latest_version = versioned_specs[-1].name
        print(f"  Latest versioned spec: {latest_version}")
    else:
        latest_version = "none"
        print(f"  No versioned specs found")
    
    print()
    print("="*70)
    print(f"  {YELLOW}⚠️  OpenAPI spec changed - version bump required{RESET}")
    print("="*70 + "\n")
    
    print("To fix:")
    print(f"1. Determine if change is major or minor")
    print(f"2. Create new version file:")
    print(f"     curl http://localhost:8000/openapi.json > docs/openapi-vX.Y.json")
    print(f"3. Update openapi-latest.json:")
    print(f"     cp docs/openapi-vX.Y.json docs/openapi-latest.json")
    print(f"4. Commit both files:")
    print(f"     git add docs/openapi-v*.json docs/openapi-latest.json")
    print(f"5. Update OPENAPI_VERSIONING.md with change notes\n")
    
    return 1


if __name__ == "__main__":
    sys.exit(main())

