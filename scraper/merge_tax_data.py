#!/usr/bin/env python3
"""
Merge Tax Data with Nomenclature

Merges the tax information from tax_responses/ with the processed nomenclature data.
Creates enhanced versions with tax_info field added to each item.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Configuration
TAX_RESPONSES_DIR = "tax_responses"
DATA_DIR = "data"
FLAT_INPUT = "nomenclature_flat.json"
TREE_INPUT = "nomenclature_tree.json"
FLAT_OUTPUT = "nomenclature_flat_with_tax.json"
TREE_OUTPUT = "nomenclature_tree_with_tax.json"
LOGS_DIR = "logs"

# Setup logging
log_file = Path(LOGS_DIR) / f"merge_tax_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
log_file.parent.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TaxDataMerger:
    def __init__(self):
        self.tax_dir = Path(TAX_RESPONSES_DIR)
        self.data_dir = Path(DATA_DIR)
        self.tax_by_nc: Dict[str, dict] = {}

    def load_tax_responses(self):
        """Load all tax responses and index by NC code"""
        logger.info(f"Loading tax responses from {self.tax_dir}")

        if not self.tax_dir.exists():
            logger.warning(f"Tax responses directory not found: {self.tax_dir}")
            logger.warning("Run tax_scraper.py first to fetch tax data")
            return

        json_files = list(self.tax_dir.glob("*.json"))
        logger.info(f"Found {len(json_files)} tax response files")

        loaded = 0
        with_data = 0

        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    results = data.get('results', [])

                    if results:
                        # Extract NC code from first result
                        nc_code = results[0].get('tarim', {}).get('nc', '')
                        if nc_code:
                            # Store the full tax data
                            self.tax_by_nc[nc_code] = results[0]
                            with_data += 1

                    loaded += 1

                    if loaded % 1000 == 0:
                        logger.info(f"Progress: loaded {loaded}/{len(json_files)} files")

            except Exception as e:
                logger.error(f"Error loading {json_file}: {e}")

        logger.info(f"Loaded {loaded} tax response files")
        logger.info(f"Found tax data for {with_data} NC codes")

    def extract_tax_info(self, tax_data: dict) -> dict:
        """Extract relevant tax information from API response"""
        if not tax_data:
            return {}

        return {
            'vat': tax_data.get('vat', ''),
            'excise': tax_data.get('excise', ''),
            'vat_exemption_ro': tax_data.get('i18n', {}).get('ro', {}).get('vat_exemption', ''),
            'vat_exemption_ru': tax_data.get('i18n', {}).get('ru', {}).get('vat_exemption', ''),
            'vat_exemption_en': tax_data.get('i18n', {}).get('en', {}).get('vat_exemption', ''),
            'tax_customs_ro': tax_data.get('i18n', {}).get('ro', {}).get('tax_customs', ''),
            'tax_customs_ru': tax_data.get('i18n', {}).get('ru', {}).get('tax_customs', ''),
            'tax_customs_en': tax_data.get('i18n', {}).get('en', {}).get('tax_customs', ''),
            'excise_exempted_ro': tax_data.get('i18n', {}).get('ro', {}).get('excise_exempted', ''),
            'excise_exempted_ru': tax_data.get('i18n', {}).get('ru', {}).get('excise_exempted', ''),
            'excise_exempted_en': tax_data.get('i18n', {}).get('en', {}).get('excise_exempted', ''),
            'export_ro': tax_data.get('i18n', {}).get('ro', {}).get('export', ''),
            'export_ru': tax_data.get('i18n', {}).get('ru', {}).get('export', ''),
            'export_en': tax_data.get('i18n', {}).get('en', {}).get('export', ''),
            'tax_values': tax_data.get('taxvalues_set', []),
            'valid_from': tax_data.get('valid_from', ''),
            'valid_to': tax_data.get('valid_to', ''),
        }

    def merge_flat_data(self) -> List[dict]:
        """Merge tax data with flat nomenclature structure"""
        logger.info("Merging tax data with flat structure...")

        flat_file = self.data_dir / FLAT_INPUT
        if not flat_file.exists():
            logger.error(f"Flat data file not found: {flat_file}")
            logger.error("Run processor.py first")
            return []

        with open(flat_file, 'r', encoding='utf-8') as f:
            flat_data = json.load(f)

        logger.info(f"Loaded {len(flat_data)} items from flat structure")

        merged_count = 0
        for item in flat_data:
            nc_code = item.get('nc', '')
            if nc_code and nc_code in self.tax_by_nc:
                item['tax_info'] = self.extract_tax_info(self.tax_by_nc[nc_code])
                merged_count += 1

        logger.info(f"Merged tax data for {merged_count}/{len(flat_data)} items")
        return flat_data

    def merge_tree_data(self, tree: List[dict]) -> List[dict]:
        """Recursively merge tax data with tree structure"""
        for item in tree:
            nc_code = item.get('nc', '')
            if nc_code and nc_code in self.tax_by_nc:
                item['tax_info'] = self.extract_tax_info(self.tax_by_nc[nc_code])

            # Recursively process children
            if 'children' in item:
                self.merge_tree_data(item['children'])

        return tree

    def save_outputs(self, flat_data: List[dict], tree_data: List[dict]):
        """Save merged data to JSON files"""
        logger.info("Saving merged outputs...")

        # Save flattened structure with tax
        flat_output = self.data_dir / FLAT_OUTPUT
        with open(flat_output, 'w', encoding='utf-8') as f:
            json.dump(flat_data, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved merged flat data to {flat_output}")
        logger.info(f"File size: {flat_output.stat().st_size / 1024 / 1024:.2f} MB")

        # Save tree structure with tax
        tree_output = self.data_dir / TREE_OUTPUT
        with open(tree_output, 'w', encoding='utf-8') as f:
            json.dump(tree_data, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved merged tree data to {tree_output}")
        logger.info(f"File size: {tree_output.stat().st_size / 1024 / 1024:.2f} MB")

    def run(self):
        """Run the merge process"""
        logger.info("=" * 60)
        logger.info("Starting Tax Data Merger")
        logger.info("=" * 60)

        try:
            # Load tax responses
            self.load_tax_responses()

            if not self.tax_by_nc:
                logger.warning("No tax data loaded. Output will be same as input.")

            # Merge with flat structure
            flat_data = self.merge_flat_data()

            # Load and merge with tree structure
            logger.info("Merging tax data with tree structure...")
            tree_file = self.data_dir / TREE_INPUT
            if tree_file.exists():
                with open(tree_file, 'r', encoding='utf-8') as f:
                    tree_data = json.load(f)
                logger.info(f"Loaded tree structure with {len(tree_data)} root items")
                tree_data = self.merge_tree_data(tree_data)
            else:
                logger.error(f"Tree data file not found: {tree_file}")
                tree_data = []

            # Save merged outputs
            if flat_data:
                self.save_outputs(flat_data, tree_data)

            logger.info("=" * 60)
            logger.info("Merge completed successfully!")
            logger.info(f"Merged flat data: {self.data_dir / FLAT_OUTPUT}")
            logger.info(f"Merged tree data: {self.data_dir / TREE_OUTPUT}")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"Merge failed: {e}", exc_info=True)


if __name__ == "__main__":
    merger = TaxDataMerger()
    merger.run()
