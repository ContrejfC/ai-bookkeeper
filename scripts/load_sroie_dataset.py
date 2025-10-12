#!/usr/bin/env python3
"""
SROIE Dataset Loader

Loads SROIE (Scanned Receipts OCR and Information Extraction) dataset
and generates sample receipt data for testing.

SROIE Format:
- Images: *.jpg
- Labels: *.txt (JSON format with company, date, address, total)

Usage:
    python scripts/load_sroie_dataset.py --limit 1000
    python scripts/load_sroie_dataset.py --generate-samples 100
"""
import sys
import argparse
import json
import csv
import logging
from pathlib import Path
from datetime import datetime, timedelta
import uuid
import random

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SROIELoader:
    """Loader for SROIE dataset."""
    
    def __init__(self, data_dir: Path, output_dir: Path):
        """
        Initialize SROIE loader.
        
        Args:
            data_dir: Directory containing SROIE images and labels
            output_dir: Output directory for processed data
        """
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.images_dir = self.output_dir / "images"
        self.labels_dir = self.output_dir / "labels"
        self.images_dir.mkdir(exist_ok=True)
        self.labels_dir.mkdir(exist_ok=True)
    
    def load_dataset(self, limit: int = None) -> list:
        """
        Load SROIE dataset from directory.
        
        Args:
            limit: Maximum number of receipts to load
            
        Returns:
            List of receipt metadata dicts
        """
        logger.info(f"Loading SROIE dataset from {self.data_dir}")
        
        # Find all image files
        image_files = list(self.data_dir.glob("*.jpg")) + list(self.data_dir.glob("*.png"))
        
        if not image_files:
            logger.warning(f"No image files found in {self.data_dir}")
            return []
        
        if limit:
            image_files = image_files[:limit]
        
        logger.info(f"Found {len(image_files)} receipt images")
        
        receipts = []
        for image_path in image_files:
            # Look for corresponding label file
            label_path = image_path.with_suffix('.txt')
            
            if label_path.exists():
                label_data = self._parse_label_file(label_path)
            else:
                logger.warning(f"No label file for {image_path.name}")
                label_data = {}
            
            # Generate document ID
            document_id = uuid.uuid4().hex
            
            receipt = {
                'document_id': document_id,
                'image_path': str(image_path),
                'label_path': str(label_path) if label_path.exists() else None,
                'label_vendor': label_data.get('company', ''),
                'label_date': label_data.get('date', ''),
                'label_amount': label_data.get('total', 0.0),
                'label_address': label_data.get('address', '')
            }
            
            receipts.append(receipt)
        
        return receipts
    
    def _parse_label_file(self, label_path: Path) -> dict:
        """
        Parse SROIE label file.
        
        SROIE label format (JSON):
        {
          "company": "VENDOR NAME",
          "date": "DD/MM/YYYY",
          "address": "...",
          "total": "123.45"
        }
        
        Args:
            label_path: Path to label file
            
        Returns:
            Dict with parsed label data
        """
        try:
            with open(label_path, 'r') as f:
                data = json.load(f)
            
            # Normalize total to float
            if 'total' in data:
                total_str = str(data['total']).replace(',', '').replace('$', '').strip()
                try:
                    data['total'] = float(total_str)
                except ValueError:
                    data['total'] = 0.0
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to parse label file {label_path}: {e}")
            return {}
    
    def save_metadata_csv(self, receipts: list, output_path: Path):
        """Save receipt metadata to CSV."""
        logger.info(f"Saving metadata to {output_path}")
        
        # Get all unique fieldnames from receipts
        fieldnames = set()
        for receipt in receipts:
            fieldnames.update(receipt.keys())
        
        fieldnames = sorted(list(fieldnames))
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(receipts)
        
        logger.info(f"Saved {len(receipts)} receipts to {output_path}")


class SampleReceiptGenerator:
    """Generate sample receipt data for testing."""
    
    VENDORS = [
        'Starbucks Coffee', 'Walmart Supercenter', 'Target', 'CVS Pharmacy',
        'Walgreens', '7-Eleven', 'Shell Gas Station', 'McDonald\'s',
        'Subway', 'Costco Wholesale', 'Home Depot', 'Lowe\'s',
        'Best Buy', 'Staples', 'Office Depot', 'Amazon', 'FedEx Office'
    ]
    
    CATEGORIES = {
        'Starbucks Coffee': ('Food & Dining', (3.50, 15.00)),
        'Walmart Supercenter': ('Retail', (20.00, 150.00)),
        'Target': ('Retail', (15.00, 120.00)),
        'CVS Pharmacy': ('Healthcare', (10.00, 80.00)),
        'Shell Gas Station': ('Transportation', (30.00, 90.00)),
        'McDonald\'s': ('Food & Dining', (5.00, 25.00)),
        'Costco Wholesale': ('Retail', (50.00, 300.00)),
        'Home Depot': ('Retail', (25.00, 200.00)),
        'Best Buy': ('Electronics', (30.00, 500.00)),
        'Staples': ('Office Supplies', (15.00, 150.00)),
        'FedEx Office': ('Business Services', (10.00, 100.00)),
    }
    
    def __init__(self, output_dir: Path):
        """
        Initialize sample receipt generator.
        
        Args:
            output_dir: Output directory
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_samples(self, count: int = 100) -> list:
        """
        Generate sample receipt data.
        
        Args:
            count: Number of samples to generate
            
        Returns:
            List of receipt metadata dicts
        """
        logger.info(f"Generating {count} sample receipts")
        
        receipts = []
        start_date = datetime.now() - timedelta(days=365)
        
        for i in range(count):
            vendor = random.choice(self.VENDORS)
            category_info = self.CATEGORIES.get(vendor, ('General', (10.00, 100.00)))
            category, (min_amt, max_amt) = category_info
            
            amount = round(random.uniform(min_amt, max_amt), 2)
            date = start_date + timedelta(days=random.randint(0, 365))
            
            document_id = uuid.uuid4().hex
            
            receipt = {
                'document_id': document_id,
                'image_path': f"sample_{document_id}.jpg",
                'label_path': f"sample_{document_id}.txt",
                'label_vendor': vendor,
                'label_date': date.strftime('%Y-%m-%d'),
                'label_amount': amount,
                'label_address': f"{random.randint(100, 9999)} Main St, City, ST {random.randint(10000, 99999)}",
                'category': category
            }
            
            receipts.append(receipt)
        
        logger.info(f"Generated {len(receipts)} sample receipts")
        return receipts
    
    def save_sample_labels(self, receipts: list):
        """Save sample labels as JSON files."""
        labels_dir = self.output_dir / "labels"
        labels_dir.mkdir(exist_ok=True)
        
        for receipt in receipts:
            label_file = labels_dir / receipt['label_path']
            
            label_data = {
                'company': receipt['label_vendor'],
                'date': receipt['label_date'],
                'total': receipt['label_amount'],
                'address': receipt['label_address']
            }
            
            with open(label_file, 'w') as f:
                json.dump(label_data, f, indent=2)


def main():
    """Main loader script."""
    parser = argparse.ArgumentParser(description='Load SROIE dataset or generate samples')
    parser.add_argument(
        '--data-dir',
        default='data/sroie',
        help='SROIE dataset directory (default: data/sroie)'
    )
    parser.add_argument(
        '--output-dir',
        default='data/ocr',
        help='Output directory (default: data/ocr)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of receipts to load'
    )
    parser.add_argument(
        '--generate-samples',
        type=int,
        default=None,
        metavar='COUNT',
        help='Generate sample receipts instead of loading SROIE'
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("  SROIE DATASET LOADER")
    print("="*70 + "\n")
    
    output_dir = Path(args.output_dir)
    
    if args.generate_samples:
        # Generate sample data
        generator = SampleReceiptGenerator(output_dir)
        receipts = generator.generate_samples(args.generate_samples)
        generator.save_sample_labels(receipts)
        
        # Save metadata CSV
        metadata_path = output_dir / "sample_receipts_metadata.csv"
        loader = SROIELoader(Path(args.data_dir), output_dir)
        loader.save_metadata_csv(receipts, metadata_path)
        
        print(f"\n✅ Generated {len(receipts)} sample receipts")
        print(f"   Labels: {output_dir}/labels/")
        print(f"   Metadata: {metadata_path}")
        
    else:
        # Load SROIE dataset
        loader = SROIELoader(Path(args.data_dir), output_dir)
        receipts = loader.load_dataset(limit=args.limit)
        
        if receipts:
            metadata_path = output_dir / "sroie_metadata.csv"
            loader.save_metadata_csv(receipts, metadata_path)
            
            print(f"\n✅ Loaded {len(receipts)} receipts from SROIE dataset")
            print(f"   Metadata: {metadata_path}")
        else:
            print(f"\n⚠️  No receipts found in {args.data_dir}")
            print(f"   Try: --generate-samples 100 to create test data")
    
    print("\n" + "="*70)
    return 0


if __name__ == "__main__":
    sys.exit(main())

