#!/usr/bin/env python3
"""
Generate Stage B receipts with 8-10% OCR-like noise (Sprint 9).

Noise Recipe:
- Typos: 5% (character swaps, missing chars, extra chars)
- Casing: 3% (random case changes, ALL CAPS words)
- Spacing/Punctuation: 2% (double spaces, missing/extra punctuation)

Total: 8-10% of characters affected

Fixed seeds per tenant for reproducibility:
- Tenant Alpha: seed=5001
- Tenant Beta: seed=5002

Output:
- tests/fixtures/receipts/alpha/*.txt (300+ receipts)
- tests/fixtures/receipts/beta/*.txt (300+ receipts)
- NOISE_RECIPE.md (documentation)
"""
import sys
import random
import string
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Tuple
import hashlib

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configuration
ALPHA_SEED = 5001
BETA_SEED = 5002
MIN_RECEIPTS_PER_TENANT = 300

# Noise percentages (must sum to 8-10%)
TYPO_RATE = 0.05      # 5%
CASING_RATE = 0.03    # 3%
SPACING_RATE = 0.02   # 2%
TOTAL_NOISE_RATE = TYPO_RATE + CASING_RATE + SPACING_RATE  # 10%

# Receipt templates
RECEIPT_TEMPLATES = [
    # Retail
    """
    {vendor_name}
    {address}
    {city}, {state} {zip}
    
    Date: {date}
    Time: {time}
    Receipt: #{receipt_id}
    
    {items}
    
    Subtotal:    ${subtotal:.2f}
    Tax:         ${tax:.2f}
    Total:       ${total:.2f}
    
    Payment: {payment_method}
    Card: ****{card_last4}
    
    Thank you for your business!
    """,
    
    # Invoice
    """
    INVOICE
    
    From: {vendor_name}
          {address}
          {city}, {state} {zip}
          Phone: {phone}
    
    Invoice #: {invoice_id}
    Date: {date}
    Due Date: {due_date}
    
    Bill To: {customer_name}
    
    Description                      Amount
    ----------------------------------------
    {items}
    ----------------------------------------
    
    Subtotal:                    ${subtotal:.2f}
    Tax:                         ${tax:.2f}
    Total Due:                   ${total:.2f}
    
    Please remit payment by {due_date}
    """,
    
    # Service Receipt
    """
    {vendor_name}
    Service Receipt
    
    Date: {date}
    Job #: {job_id}
    
    Customer: {customer_name}
    Address: {service_address}
    
    Services Provided:
    {items}
    
    Labor:       ${labor:.2f}
    Materials:   ${materials:.2f}
    Subtotal:    ${subtotal:.2f}
    Tax:         ${tax:.2f}
    Total:       ${total:.2f}
    
    Payment Received: ${total:.2f}
    Method: {payment_method}
    
    Authorized by: {technician}
    """
]


def apply_typo_noise(text: str, rate: float, rng: random.Random) -> str:
    """Apply typo noise: character swaps, deletions, insertions."""
    chars = list(text)
    num_chars = len(chars)
    num_typos = int(num_chars * rate)
    
    for _ in range(num_typos):
        if num_chars == 0:
            break
        
        pos = rng.randint(0, num_chars - 1)
        typo_type = rng.choice(['swap', 'delete', 'insert'])
        
        if typo_type == 'swap' and pos < num_chars - 1 and chars[pos].isalpha() and chars[pos + 1].isalpha():
            # Swap adjacent characters
            chars[pos], chars[pos + 1] = chars[pos + 1], chars[pos]
        elif typo_type == 'delete' and chars[pos].isalpha():
            # Delete character
            chars.pop(pos)
            num_chars -= 1
        elif typo_type == 'insert' and chars[pos].isalpha():
            # Insert random character
            insert_char = rng.choice(string.ascii_lowercase)
            chars.insert(pos, insert_char)
            num_chars += 1
    
    return ''.join(chars)


def apply_casing_noise(text: str, rate: float, rng: random.Random) -> str:
    """Apply casing noise: random case changes, ALL CAPS words."""
    words = text.split()
    num_words = len(words)
    num_casing_changes = int(num_words * rate)
    
    for _ in range(num_casing_changes):
        if num_words == 0:
            break
        
        pos = rng.randint(0, num_words - 1)
        word = words[pos]
        
        if not word or not any(c.isalpha() for c in word):
            continue
        
        casing_type = rng.choice(['upper', 'lower', 'random'])
        
        if casing_type == 'upper':
            words[pos] = word.upper()
        elif casing_type == 'lower':
            words[pos] = word.lower()
        elif casing_type == 'random':
            words[pos] = ''.join(c.upper() if rng.random() > 0.5 else c.lower() for c in word)
    
    return ' '.join(words)


def apply_spacing_noise(text: str, rate: float, rng: random.Random) -> str:
    """Apply spacing/punctuation noise: double spaces, missing/extra punctuation."""
    chars = list(text)
    num_chars = len(chars)
    num_spacing_changes = int(num_chars * rate)
    
    for _ in range(num_spacing_changes):
        if num_chars == 0:
            break
        
        pos = rng.randint(0, num_chars - 1)
        spacing_type = rng.choice(['double_space', 'remove_punct', 'add_punct'])
        
        if spacing_type == 'double_space' and chars[pos] == ' ':
            # Double space
            chars.insert(pos, ' ')
            num_chars += 1
        elif spacing_type == 'remove_punct' and chars[pos] in ',.;:!?':
            # Remove punctuation
            chars.pop(pos)
            num_chars -= 1
        elif spacing_type == 'add_punct' and chars[pos].isalpha() and pos < num_chars - 1:
            # Add random punctuation
            punct = rng.choice(',.;')
            chars.insert(pos + 1, punct)
            num_chars += 1
    
    return ''.join(chars)


def apply_ocr_noise(text: str, seed: int) -> Tuple[str, float]:
    """Apply OCR-like noise to text with exact percentages."""
    rng = random.Random(seed)
    
    original_length = len(text)
    
    # Apply noise in order: typos, casing, spacing
    noisy_text = apply_typo_noise(text, TYPO_RATE, rng)
    noisy_text = apply_casing_noise(noisy_text, CASING_RATE, rng)
    noisy_text = apply_spacing_noise(noisy_text, SPACING_RATE, rng)
    
    # Calculate actual noise rate using character-level diff
    # Account for length differences by using the longer length
    max_length = max(len(text), len(noisy_text))
    min_length = min(len(text), len(noisy_text))
    
    # Count character differences in the overlapping region
    differences = sum(1 for i in range(min_length) if text[i] != noisy_text[i])
    
    # Add length difference as additional noise
    differences += (max_length - min_length)
    
    # Calculate as percentage of original length
    actual_noise_rate = differences / original_length if original_length > 0 else 0
    
    return noisy_text, actual_noise_rate


def generate_receipt(vendor: str, template_idx: int, date: datetime, seed: int) -> Tuple[str, float]:
    """Generate a single receipt with OCR noise."""
    rng = random.Random(seed)
    
    template = RECEIPT_TEMPLATES[template_idx]
    
    # Generate receipt data
    receipt_data = {
        'vendor_name': vendor,
        'address': f"{rng.randint(100, 9999)} {rng.choice(['Main', 'Oak', 'Elm', 'Maple'])} St",
        'city': rng.choice(['Cincinnati', 'Columbus', 'Cleveland', 'Toledo']),
        'state': 'OH',
        'zip': f"{rng.randint(10000, 99999)}",
        'date': date.strftime("%m/%d/%Y"),
        'due_date': (date + timedelta(days=30)).strftime("%m/%d/%Y"),
        'time': f"{rng.randint(8, 20):02d}:{rng.randint(0, 59):02d}",
        'receipt_id': f"{rng.randint(1000, 9999)}",
        'invoice_id': f"INV-{rng.randint(10000, 99999)}",
        'job_id': f"JOB-{rng.randint(1000, 9999)}",
        'phone': f"({rng.randint(100, 999)}) {rng.randint(100, 999)}-{rng.randint(1000, 9999)}",
        'customer_name': rng.choice(['ABC Company', 'XYZ Corp', 'Smith Industries', 'Johnson LLC']),
        'service_address': f"{rng.randint(100, 9999)} Business Pkwy",
        'payment_method': rng.choice(['Credit Card', 'Debit Card', 'Check', 'Cash']),
        'card_last4': f"{rng.randint(1000, 9999)}",
        'technician': rng.choice(['John Smith', 'Jane Doe', 'Bob Johnson']),
    }
    
    # Generate items
    num_items = rng.randint(1, 5)
    items_list = []
    subtotal = 0.0
    
    for i in range(num_items):
        item_name = rng.choice(['Office Supplies', 'Service Fee', 'Consulting', 'Materials', 'Equipment', 'Labor'])
        item_price = round(rng.uniform(10, 500), 2)
        items_list.append(f"{item_name:<30} ${item_price:>8.2f}")
        subtotal += item_price
    
    receipt_data['items'] = '\n'.join(items_list)
    receipt_data['subtotal'] = subtotal
    receipt_data['labor'] = round(subtotal * 0.6, 2)
    receipt_data['materials'] = round(subtotal * 0.4, 2)
    receipt_data['tax'] = round(subtotal * 0.07, 2)
    receipt_data['total'] = round(subtotal + receipt_data['tax'], 2)
    
    # Format receipt
    clean_receipt = template.format(**receipt_data).strip()
    
    # Apply OCR noise
    noisy_receipt, noise_rate = apply_ocr_noise(clean_receipt, seed)
    
    return noisy_receipt, noise_rate


def generate_receipts_for_tenant(tenant_name: str, tenant_id: str, seed: int, num_receipts: int) -> List[Tuple[str, float]]:
    """Generate receipts for a tenant."""
    rng = random.Random(seed)
    
    vendors = [
        "Office Depot", "Staples", "Amazon Business", "FedEx", "UPS",
        "AT&T", "Verizon", "Comcast", "QuickBooks", "Adobe",
        "Microsoft", "Google", "Salesforce", "AWS", "Digital Ocean"
    ]
    
    receipts = []
    start_date = datetime.now() - timedelta(days=365)
    
    for i in range(num_receipts):
        vendor = rng.choice(vendors)
        template_idx = rng.randint(0, len(RECEIPT_TEMPLATES) - 1)
        days_offset = rng.randint(0, 365)
        date = start_date + timedelta(days=days_offset)
        receipt_seed = seed + i
        
        receipt_text, noise_rate = generate_receipt(vendor, template_idx, date, receipt_seed)
        receipts.append((receipt_text, noise_rate))
    
    return receipts


def write_receipts(tenant_name: str, tenant_id: str, receipts: List[Tuple[str, float]], output_dir: Path):
    """Write receipts to files."""
    tenant_dir = output_dir / tenant_id
    tenant_dir.mkdir(parents=True, exist_ok=True)
    
    noise_rates = []
    
    for idx, (receipt_text, noise_rate) in enumerate(receipts):
        receipt_path = tenant_dir / f"receipt_{idx+1:04d}.txt"
        with open(receipt_path, "w") as f:
            f.write(receipt_text)
        noise_rates.append(noise_rate)
    
    avg_noise_rate = sum(noise_rates) / len(noise_rates) if noise_rates else 0
    
    print(f"  ✅ Wrote {len(receipts)} receipts to {tenant_dir}")
    print(f"     Average noise rate: {avg_noise_rate:.2%} (target: 8-10%)")
    
    return avg_noise_rate


def write_noise_recipe_doc(output_dir: Path, alpha_noise: float, beta_noise: float):
    """Document the noise recipe."""
    doc_path = output_dir / "NOISE_RECIPE.md"
    
    with open(doc_path, "w") as f:
        f.write("# OCR Noise Recipe (Sprint 9 Stage B)\n\n")
        f.write("**Generated:** " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n\n")
        
        f.write("## Noise Percentages\n\n")
        f.write(f"- **Typos:** {TYPO_RATE:.1%} (character swaps, deletions, insertions)\n")
        f.write(f"- **Casing:** {CASING_RATE:.1%} (random case changes, ALL CAPS words)\n")
        f.write(f"- **Spacing/Punctuation:** {SPACING_RATE:.1%} (double spaces, missing/extra punctuation)\n")
        f.write(f"- **Total Target:** {TOTAL_NOISE_RATE:.1%}\n\n")
        
        f.write("## Typo Noise (5%)\n\n")
        f.write("Applied to individual characters:\n")
        f.write("- **Character swaps:** Adjacent letters swapped (e.g., 'hte' → 'the')\n")
        f.write("- **Character deletions:** Random letters removed (e.g., 'total' → 'tota')\n")
        f.write("- **Character insertions:** Random letters added (e.g., 'date' → 'datre')\n\n")
        
        f.write("## Casing Noise (3%)\n\n")
        f.write("Applied to words:\n")
        f.write("- **ALL CAPS:** Entire word uppercased (e.g., 'Invoice' → 'INVOICE')\n")
        f.write("- **all lower:** Entire word lowercased (e.g., 'Total' → 'total')\n")
        f.write("- **RaNdOm:** Random case per character (e.g., 'Receipt' → 'rEcEiPt')\n\n")
        
        f.write("## Spacing/Punctuation Noise (2%)\n\n")
        f.write("Applied to whitespace and punctuation:\n")
        f.write("- **Double spaces:** Single space → double space\n")
        f.write("- **Missing punctuation:** Punctuation removed (e.g., 'Total: $100' → 'Total $100')\n")
        f.write("- **Extra punctuation:** Random punctuation added (e.g., 'Date 10/11' → 'Date, 10/11')\n\n")
        
        f.write("## Actual Noise Rates (Measured)\n\n")
        f.write(f"- **Tenant Alpha:** {alpha_noise:.2%}\n")
        f.write(f"- **Tenant Beta:** {beta_noise:.2%}\n")
        f.write(f"- **Average:** {(alpha_noise + beta_noise) / 2:.2%}\n\n")
        
        f.write("## Reproducibility\n\n")
        f.write("Fixed seeds ensure deterministic generation:\n")
        f.write(f"- **Alpha seed:** {ALPHA_SEED}\n")
        f.write(f"- **Beta seed:** {BETA_SEED}\n\n")
        f.write("To regenerate identical receipts:\n")
        f.write("```bash\n")
        f.write("python scripts/generate_stage_b_receipts.py\n")
        f.write("```\n")
    
    print(f"\n  ✅ Wrote noise recipe documentation: {doc_path}")


def main():
    """Generate Stage B receipts with OCR noise."""
    fixtures_dir = Path(__file__).parent.parent / "tests" / "fixtures" / "receipts"
    
    print(f"\n{'='*80}")
    print("STAGE B RECEIPTS GENERATOR (with OCR Noise)")
    print(f"{'='*80}\n")
    
    print(f"Noise Configuration:")
    print(f"  Typos: {TYPO_RATE:.1%}")
    print(f"  Casing: {CASING_RATE:.1%}")
    print(f"  Spacing/Punctuation: {SPACING_RATE:.1%}")
    print(f"  Total: {TOTAL_NOISE_RATE:.1%}")
    print("")
    
    # Generate Tenant Alpha
    print(f"Generating Tenant Alpha (seed={ALPHA_SEED})...")
    alpha_receipts = generate_receipts_for_tenant("Alpha Manufacturing", "alpha", ALPHA_SEED, MIN_RECEIPTS_PER_TENANT)
    alpha_noise = write_receipts("Alpha Manufacturing", "alpha", alpha_receipts, fixtures_dir)
    
    # Generate Tenant Beta
    print(f"\nGenerating Tenant Beta (seed={BETA_SEED})...")
    beta_receipts = generate_receipts_for_tenant("Beta Services", "beta", BETA_SEED, MIN_RECEIPTS_PER_TENANT)
    beta_noise = write_receipts("Beta Services", "beta", beta_receipts, fixtures_dir)
    
    # Write documentation
    write_noise_recipe_doc(fixtures_dir, alpha_noise, beta_noise)
    
    # Summary
    total_receipts = len(alpha_receipts) + len(beta_receipts)
    avg_noise = (alpha_noise + beta_noise) / 2
    
    print(f"\n{'='*80}")
    print(f"✅ STAGE B RECEIPTS COMPLETE")
    print(f"{'='*80}\n")
    print(f"Total Receipts: {total_receipts}")
    print(f"  - Tenant Alpha: {len(alpha_receipts)}")
    print(f"  - Tenant Beta: {len(beta_receipts)}")
    print(f"\nAverage Noise Rate: {avg_noise:.2%} (target: 8-10%)")
    print(f"\nReceipts Location: {fixtures_dir}")
    print(f"  - alpha/*.txt")
    print(f"  - beta/*.txt")
    print(f"  - NOISE_RECIPE.md")
    
    # Validation
    if 0.08 <= avg_noise <= 0.10:
        print(f"\n✅ Noise rate within target range (8-10%)")
    else:
        print(f"\n⚠️  Noise rate {avg_noise:.2%} outside target range (8-10%)")
    
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    main()

