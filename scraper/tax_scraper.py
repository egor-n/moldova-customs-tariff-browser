#!/usr/bin/env python3
"""
Moldova Tariff Tax Information Scraper

Fetches tax information for all NC codes from trade.gov.md API.
Designed for ~15,000 requests with resume capability and robust error handling.
"""

import requests
import json
import time
import os
import logging
from pathlib import Path
from datetime import datetime
import random

# Configuration
TAX_API_URL = "https://trade.gov.md/api/tarim_tax/"
RAW_RESPONSES_DIR = "raw_responses"
TAX_RESPONSES_DIR = "tax_responses"
DATA_DIR = "data"
LOGS_DIR = "logs"
MIN_DELAY = 1.0  # seconds between requests
MAX_DELAY = 1.5  # random jitter upper bound
MAX_RETRIES = 3
BACKOFF_FACTOR = 2

# Setup logging
os.makedirs(LOGS_DIR, exist_ok=True)
log_file = os.path.join(LOGS_DIR, f"tax_scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TaxScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:144.0) Gecko/20100101 Firefox/144.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'All',
        })
        self.tax_dir = Path(TAX_RESPONSES_DIR)
        self.tax_dir.mkdir(exist_ok=True)
        self.total_requests = 0
        self.total_success = 0
        self.total_empty = 0
        self.total_errors = 0

    def load_nc_codes(self) -> list:
        """Load all NC codes from processed nomenclature data"""
        flat_file = Path(DATA_DIR) / "nomenclature_flat.json"
        tree_file = Path(DATA_DIR) / "nomenclature_tree.json"

        # Try flat file first, then tree file
        data_file = flat_file if flat_file.exists() else tree_file

        if not data_file.exists():
            logger.error(f"No processed data found. Please run processor.py first.")
            logger.error(f"Expected: {flat_file} or {tree_file}")
            return []

        logger.info(f"Loading NC codes from: {data_file}")

        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Extract NC codes (handle both flat array and tree structure)
        nc_codes = set()

        def extract_codes(items):
            for item in items:
                nc = item.get('nc', '').strip()
                if nc:  # Only add non-empty NC codes
                    nc_codes.add(nc)
                # Recursively process children if tree structure
                if 'children' in item and isinstance(item['children'], list):
                    extract_codes(item['children'])

        extract_codes(data if isinstance(data, list) else [data])

        codes_list = sorted(nc_codes)
        logger.info(f"Found {len(codes_list)} unique NC codes")
        return codes_list

    def get_response_filename(self, nc_code: str) -> Path:
        """Generate filename for saving tax response"""
        # Use NC code as filename (safe for filesystem)
        safe_filename = nc_code.replace('/', '_').replace('\\', '_')
        return self.tax_dir / f"{safe_filename}.json"

    def fetch_tax_info(self, nc_code: str) -> dict | None:
        """Fetch tax information for a single NC code"""
        params = {
            'tarim__nc': nc_code
        }

        filename = self.get_response_filename(nc_code)

        # Check if already fetched
        if filename.exists():
            logger.debug(f"Skipping {nc_code} (already exists)")
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)

        # Make request with retries
        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"Fetching tax info for {nc_code} (attempt {attempt + 1})")
                response = self.session.get(TAX_API_URL, params=params, timeout=30)

                if response.status_code == 429:
                    wait_time = BACKOFF_FACTOR ** attempt * 10
                    logger.warning(f"Rate limited (429). Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                if response.status_code == 404:
                    logger.info(f"No tax info found for {nc_code} (404)")
                    # Save empty response
                    empty_data = {"nc_code": nc_code, "results": []}
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(empty_data, f, ensure_ascii=False, indent=2)
                    return empty_data

                response.raise_for_status()
                data = response.json()

                # Save response
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

                self.total_requests += 1

                if data.get('count', 0) > 0:
                    self.total_success += 1
                    logger.info(f"✓ Saved tax info for {nc_code} ({data['count']} results)")
                else:
                    self.total_empty += 1
                    logger.info(f"○ No tax data for {nc_code}")

                # Rate limiting delay
                delay = random.uniform(MIN_DELAY, MAX_DELAY)
                time.sleep(delay)

                return data

            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed for {nc_code} (attempt {attempt + 1}): {e}")
                if attempt < MAX_RETRIES - 1:
                    wait_time = BACKOFF_FACTOR ** attempt
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to fetch {nc_code} after {MAX_RETRIES} attempts")
                    self.total_errors += 1
                    return None

        return None

    def scrape_all(self, nc_codes: list, start_from: int = 0):
        """Scrape tax info for all NC codes"""
        total = len(nc_codes)

        if start_from > 0:
            logger.info(f"Resuming from index {start_from}")
            nc_codes = nc_codes[start_from:]

        for idx, nc_code in enumerate(nc_codes, start=start_from):
            self.fetch_tax_info(nc_code)

            # Progress report every 100 items
            if (idx + 1) % 100 == 0:
                progress_pct = ((idx + 1) / total) * 100
                logger.info(f"Progress: {idx + 1}/{total} ({progress_pct:.1f}%) - "
                          f"Success: {self.total_success}, Empty: {self.total_empty}, Errors: {self.total_errors}")

    def run(self, dry_run: bool = False, start_from: int = 0):
        """Start the tax scraping process"""
        logger.info("=" * 60)
        logger.info("Starting Moldova Tax Information Scraper")
        logger.info(f"Tax responses will be saved to: {self.tax_dir.absolute()}")
        logger.info(f"Dry run mode: {dry_run}")
        logger.info("=" * 60)

        # Load NC codes
        nc_codes = self.load_nc_codes()
        if not nc_codes:
            logger.error("No NC codes found. Exiting.")
            return

        if dry_run:
            logger.info(f"DRY RUN: Would fetch tax info for {len(nc_codes)} NC codes")
            logger.info(f"Estimated time: ~{len(nc_codes) * 1.25 / 60:.1f} minutes")
            logger.info(f"Testing with first 3 codes: {nc_codes[:3]}")

            for nc_code in nc_codes[:3]:
                self.fetch_tax_info(nc_code)

            logger.info(f"Dry run complete. Success: {self.total_success}, Empty: {self.total_empty}")
            return

        try:
            self.scrape_all(nc_codes, start_from=start_from)

            logger.info("=" * 60)
            logger.info("Tax scraping completed!")
            logger.info(f"Total requests: {self.total_requests}")
            logger.info(f"Successful: {self.total_success}")
            logger.info(f"Empty results: {self.total_empty}")
            logger.info(f"Errors: {self.total_errors}")
            logger.info(f"Tax responses saved to: {self.tax_dir.absolute()}")
            logger.info("=" * 60)

        except KeyboardInterrupt:
            logger.info("\n" + "=" * 60)
            logger.info("Scraping interrupted by user")
            logger.info(f"Progress: {self.total_requests} requests completed")
            logger.info(f"Success: {self.total_success}, Empty: {self.total_empty}, Errors: {self.total_errors}")
            logger.info("=" * 60)
            logger.info("You can resume by running:")
            logger.info(f"  python tax_scraper.py --start-from {self.total_requests}")
            logger.info("=" * 60)


if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(description='Scrape tax information for Moldova tariff nomenclature')
    parser.add_argument('--dry-run', action='store_true', help='Test with first 3 items only')
    parser.add_argument('--start-from', type=int, default=0, help='Resume from specific index')

    args = parser.parse_args()

    scraper = TaxScraper()
    scraper.run(dry_run=args.dry_run, start_from=args.start_from)
