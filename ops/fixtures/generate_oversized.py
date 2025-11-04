#!/usr/bin/env python3
"""
Generate oversized CSV file for testing ingestion robustness.
Creates a 100k row CSV to test file upload limits.
"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

def generate_oversized_csv(output_path: str, num_rows: int = 100000):
    """Generate large CSV file for testing."""
    print(f"Generating {num_rows} row CSV file...")
    
    vendors = [
        "Amazon Web Services", "Google Cloud", "Microsoft Azure",
        "Stripe", "Slack", "Zoom", "GitHub", "Dropbox",
        "Adobe", "Salesforce", "HubSpot", "Mailchimp"
    ]
    
    categories = [
        "Cloud Hosting", "Software", "Marketing", "Office Expenses",
        "Payment Processing", "Development Tools", "Utilities"
    ]
    
    start_date = datetime(2024, 1, 1)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['date', 'description', 'amount', 'vendor', 'category'])
        
        for i in range(num_rows):
            date = start_date + timedelta(days=random.randint(0, 300))
            vendor = random.choice(vendors)
            category = random.choice(categories)
            amount = round(random.uniform(10.0, 1000.0), 2)
            description = f"{vendor} - {category}"
            
            writer.writerow([
                date.strftime('%Y-%m-%d'),
                description,
                amount,
                vendor,
                category
            ])
            
            if (i + 1) % 10000 == 0:
                print(f"  Written {i + 1} rows...")
    
    print(f"✓ Generated {output_path}")

if __name__ == '__main__':
    output_path = Path(__file__).parent / 'oversized_100k_rows.csv'
    generate_oversized_csv(str(output_path))



