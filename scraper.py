#!/usr/bin/env python3
"""
Moldova Tariff Nomenclature Scraper

Scrapes the complete tariff nomenclature data from trade.gov.md API.
The API returns ALL items (with parent relationships) without needing recursive fetching.
Saves each response page as a separate JSON file for safety and resumability.
"""

import requests
import json
import time
import os
import logging
from pathlib import Path
from datetime import datetime

# Configuration
BASE_URL = "https://trade.gov.md/api/tarim-nomenclature/"
RAW_RESPONSES_DIR = "raw_responses"
LOGS_DIR = "logs"
PAGE_SIZE = 50  # API's default page size
MIN_DELAY = 2.0  # seconds between requests
MAX_DELAY = 2.5  # random jitter upper bound
MAX_RETRIES = 3
BACKOFF_FACTOR = 2

# Setup logging
os.makedirs(LOGS_DIR, exist_ok=True)
log_file = os.path.join(LOGS_DIR, f"scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TariffScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:143.0) Gecko/20100101 Firefox/143.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        self.raw_dir = Path(RAW_RESPONSES_DIR)
        self.raw_dir.mkdir(exist_ok=True)
        self.total_requests = 0
        self.total_items = 0

    def get_response_filename(self, page: int) -> Path:
        """Generate filename for saving response"""
        return self.raw_dir / f"page_{page}.json"

    def fetch_page(self, page: int = 1) -> dict | None:
        """Fetch a single page from the API"""
        params = {
            'page_size': PAGE_SIZE,
            'page': page
        }

        filename = self.get_response_filename(page)

        # Check if already fetched
        if filename.exists():
            logger.info(f"Skipping page {page} (already exists)")
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)

        # Make request with retries
        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"Fetching page {page} (attempt {attempt + 1})")
                response = self.session.get(BASE_URL, params=params, timeout=30)

                if response.status_code == 429:
                    wait_time = BACKOFF_FACTOR ** attempt * 10
                    logger.warning(f"Rate limited (429). Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                data = response.json()

                # Save response
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

                self.total_requests += 1
                logger.info(f"Saved page {page} ({len(data.get('results', []))} items)")

                # Rate limiting delay
                import random
                delay = random.uniform(MIN_DELAY, MAX_DELAY)
                time.sleep(delay)

                return data

            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < MAX_RETRIES - 1:
                    wait_time = BACKOFF_FACTOR ** attempt
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to fetch after {MAX_RETRIES} attempts")
                    return None

        return None

    def scrape_all(self):
        """Scrape all pages"""
        page = 1

        while True:
            data = self.fetch_page(page)
            if not data:
                logger.error(f"Failed to fetch page {page}")
                break

            results = data.get('results', [])
            if not results:
                logger.info(f"No results on page {page}")
                break

            self.total_items += len(results)
            logger.info(f"Progress: {self.total_items} items fetched so far")

            # Check if there are more pages
            if not data.get('next'):
                logger.info("Reached last page")
                break

            page += 1

    def run(self, dry_run: bool = False):
        """Start the scraping process"""
        logger.info("=" * 60)
        logger.info("Starting Moldova Tariff Nomenclature Scraper")
        logger.info(f"Raw responses will be saved to: {self.raw_dir.absolute()}")
        logger.info(f"Dry run mode: {dry_run}")
        logger.info("=" * 60)

        if dry_run:
            logger.info("DRY RUN: Fetching only first page to estimate scope...")
            data = self.fetch_page(1)
            if data:
                total_count = data.get('count', 0)
                results_count = len(data.get('results', []))
                pages_estimate = (total_count + PAGE_SIZE - 1) // PAGE_SIZE

                logger.info(f"Total items in database: {total_count}")
                logger.info(f"Items per page: {results_count}")
                logger.info(f"Estimated pages: ~{pages_estimate}")
                logger.info(f"Estimated time: ~{pages_estimate * 2.5 / 60:.1f} minutes")

                # Count items with children
                with_children = sum(1 for item in data.get('results', []) if item.get('children', 0) > 0)
                logger.info(f"\nItems with children on first page: {with_children}/{results_count}")
                logger.info("\nNote: The API returns ALL items (not just top-level).")
                logger.info("The 'parent' field shows relationships, but all data is in these pages.")
            return

        try:
            self.scrape_all()

            logger.info("=" * 60)
            logger.info("Scraping completed!")
            logger.info(f"Total API requests: {self.total_requests}")
            logger.info(f"Total items scraped: {self.total_items}")
            logger.info(f"Raw responses saved to: {self.raw_dir.absolute()}")
            logger.info("=" * 60)

        except KeyboardInterrupt:
            logger.info("\nScraping interrupted by user")
            logger.info(f"Progress: {self.total_requests} requests, {self.total_items} items")
            logger.info("You can resume by running the script again (existing files will be skipped)")


if __name__ == "__main__":
    import sys

    scraper = TariffScraper()

    # Check for dry-run flag
    dry_run = "--dry-run" in sys.argv

    scraper.run(dry_run=dry_run)
