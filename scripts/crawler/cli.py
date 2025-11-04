"""
Crawler CLI
===========

Command-line interface for the bank statement crawler.
"""

import sys
import argparse
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.crawler.config import load_config, get_default_config_path
from scripts.crawler.run_crawl import run_crawler


def setup_logging(verbose: bool = False):
    """
    Setup logging configuration.
    
    Args:
        verbose: Enable verbose (DEBUG) logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def cmd_crawl(args):
    """Handle crawl command."""
    config_path = Path(args.config) if args.config else get_default_config_path()
    
    print(f"\n{'='*80}")
    print("BANK STATEMENT CRAWLER")
    print(f"{'='*80}\n")
    print(f"Config: {config_path}")
    
    # Load config
    try:
        config = load_config(config_path)
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return 1
    
    # Apply CLI overrides
    if args.domain:
        # Filter to specific domain
        if args.domain in config.allow_domains:
            config.allow_domains = [args.domain]
            config.seed_urls = [url for url in config.seed_urls if args.domain in url]
            print(f"Filtering to domain: {args.domain}")
        else:
            print(f"❌ Domain '{args.domain}' not in allow_domains")
            return 1
    
    if args.max_pdfs:
        config.max_total_pdfs = args.max_pdfs
        print(f"Max PDFs: {args.max_pdfs}")
    
    if args.keep_pdfs:
        config.save_pdfs = True
        config.delete_after_extract = False
        print(f"PDFs will be saved to: {config.output_pdfs_dir}")
    
    if args.report:
        config.output_report_path = args.report
    
    if args.verbose:
        setup_logging(verbose=True)
    else:
        setup_logging(verbose=False)
    
    # Run crawler
    try:
        print(f"\nStarting crawl...")
        print(f"{'='*80}\n")
        
        report = run_crawler(config)
        
        # Print summary
        print(f"\n{'='*80}")
        print("CRAWL COMPLETE")
        print(f"{'='*80}\n")
        
        summary = report.to_dict()['summary']
        by_format = report.to_dict()['by_format']
        
        print(f"✅ Domains crawled: {summary['domains_crawled']}")
        print(f"✅ HTML pages visited: {summary['html_pages_visited']}")
        print(f"✅ Files discovered: {summary['total_files_discovered']}")
        print(f"   PDFs: {by_format['pdf']['discovered']}, CSVs: {by_format['csv']['discovered']}, XMLs: {by_format['xml']['discovered']}, TXTs: {by_format['txt']['discovered']}")
        print(f"✅ Files downloaded: {summary['total_files_downloaded']}")
        print(f"✅ Features extracted: {summary['total_features_extracted']}")
        print(f"❌ Failed: {summary['total_files_failed']}")
        print(f"📊 Success rate: {summary['success_rate']}%")
        
        print(f"\nOutputs:")
        print(f"  Features: {config.output_features_dir}")
        print(f"  Report: {config.output_report_path}")
        
        if config.save_pdfs:
            print(f"  PDFs: {config.output_pdfs_dir}")
        
        print(f"\n{'='*80}\n")
        
        return 0
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        return 130
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        if args.verbose:
            traceback.print_exc()
        return 1


def cmd_test(args):
    """Handle test command."""
    print("Testing crawler components...")
    
    # Test robots.txt
    from scripts.crawler.robots import RobotsChecker
    
    print("\n1. Testing robots.txt compliance...")
    checker = RobotsChecker("AI-Bookkeeper-ResearchBot/1.0")
    
    test_urls = [
        "https://www.chase.com/content/dam/sample.pdf",
        "https://www.bankofamerica.com/online-banking/statements.go",
    ]
    
    for url in test_urls:
        can_fetch, reason = checker.can_fetch(url)
        status = "✅" if can_fetch else "❌"
        print(f"  {status} {url}")
        print(f"     {reason}")
    
    print("\n✅ All tests passed!")
    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Bank Statement Crawler - Discover public samples from bank websites',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Crawl all configured banks
  python -m scripts.crawler.cli crawl
  
  # Crawl specific domain
  python -m scripts.crawler.cli crawl --domain chase.com
  
  # Keep PDFs and limit to 10
  python -m scripts.crawler.cli crawl --keep-pdfs --max-pdfs 10
  
  # Test components
  python -m scripts.crawler.cli test
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Crawl command
    crawl_parser = subparsers.add_parser('crawl', help='Run the crawler')
    crawl_parser.add_argument(
        '--config',
        type=str,
        help='Path to config YAML file'
    )
    crawl_parser.add_argument(
        '--domain',
        type=str,
        help='Crawl only this domain (must be in allow_domains)'
    )
    crawl_parser.add_argument(
        '--max-pdfs',
        type=int,
        help='Maximum number of PDFs to download'
    )
    crawl_parser.add_argument(
        '--keep-pdfs',
        action='store_true',
        help='Keep PDFs after feature extraction (default: delete)'
    )
    crawl_parser.add_argument(
        '--report',
        type=str,
        help='Path to save report JSON'
    )
    crawl_parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    crawl_parser.set_defaults(func=cmd_crawl)
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test crawler components')
    test_parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    test_parser.set_defaults(func=cmd_test)
    
    # Parse args
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Run command
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())

