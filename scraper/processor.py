#!/usr/bin/env python3
"""
Moldova Tariff Nomenclature Data Processor

Processes raw API responses into a flattened JSON structure optimized for AI search.
Builds complete hierarchical paths and parent chains for each item.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set
from collections import defaultdict
from datetime import datetime

# Configuration
RAW_RESPONSES_DIR = "raw_responses"
DATA_DIR = "data"
OUTPUT_FILE = "nomenclature_flat.json"
TREE_OUTPUT_FILE = "nomenclature_tree.json"
LOGS_DIR = "logs"

# Setup logging
log_file = Path(LOGS_DIR) / f"processor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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


class NomenclatureProcessor:
    def __init__(self):
        self.raw_dir = Path(RAW_RESPONSES_DIR)
        self.data_dir = Path(DATA_DIR)
        self.data_dir.mkdir(exist_ok=True)

        # Store all items by ID for building relationships
        self.items_by_id: Dict[int, dict] = {}
        self.children_by_parent: Dict[Optional[int], List[dict]] = defaultdict(list)

    def load_raw_responses(self) -> List[dict]:
        """Load all raw JSON responses"""
        logger.info(f"Loading raw responses from {self.raw_dir}")

        if not self.raw_dir.exists():
            logger.error(f"Raw responses directory not found: {self.raw_dir}")
            return []

        # Support both old naming (root_page_X.json) and new naming (page_X.json)
        json_files = (list(self.raw_dir.glob("page_*.json")) or
                     list(self.raw_dir.glob("root_page_*.json")))

        if not json_files:
            logger.error("No JSON files found in raw_responses directory")
            return []

        logger.info(f"Found {len(json_files)} response files")

        all_items = []
        for json_file in sorted(json_files):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    results = data.get('results', [])
                    all_items.extend(results)
            except Exception as e:
                logger.error(f"Error loading {json_file}: {e}")

        logger.info(f"Loaded {len(all_items)} total items")
        return all_items

    def build_lookup_tables(self, items: List[dict]):
        """Build lookup tables for items and parent-child relationships"""
        logger.info("Building lookup tables...")

        for item in items:
            item_id = item['id']
            parent_id = item.get('parent')

            self.items_by_id[item_id] = item
            self.children_by_parent[parent_id].append(item)

        logger.info(f"Indexed {len(self.items_by_id)} unique items")
        logger.info(f"Found {len(self.children_by_parent)} parent categories")

    def get_parent_chain(self, item_id: int) -> List[int]:
        """Get the full chain of parent IDs from root to this item"""
        chain = []
        current_id = item_id
        visited = set()

        while current_id is not None:
            if current_id in visited:
                logger.warning(f"Circular reference detected at item {current_id}")
                break
            visited.add(current_id)

            chain.append(current_id)
            item = self.items_by_id.get(current_id)
            if not item:
                break
            current_id = item.get('parent')

        return list(reversed(chain))  # Root to leaf order

    def get_name_path(self, item_id: int, lang: str = 'en') -> str:
        """Build a human-readable path like 'Chapter 53 > Jute > Raw jute'"""
        chain = self.get_parent_chain(item_id)
        names = []

        for id_in_chain in chain:
            item = self.items_by_id.get(id_in_chain)
            if item:
                name = item.get('i18n', {}).get(lang, {}).get('name', '')
                if name:
                    names.append(name.strip())

        return ' > '.join(names) if names else ''

    def build_flattened_structure(self, items: List[dict]) -> List[dict]:
        """Build flattened structure with full paths"""
        logger.info("Building flattened structure...")

        flattened = []

        for item in items:
            item_id = item['id']
            i18n = item.get('i18n', {})

            flattened_item = {
                'id': item_id,
                'nc': item.get('nc', ''),
                'parent_id': item.get('parent'),
                'parent_chain': self.get_parent_chain(item_id),
                'path_en': self.get_name_path(item_id, 'en'),
                'path_ro': self.get_name_path(item_id, 'ro'),
                'path_ru': self.get_name_path(item_id, 'ru'),
                'name_en': i18n.get('en', {}).get('name', ''),
                'name_ro': i18n.get('ro', {}).get('name', ''),
                'name_ru': i18n.get('ru', {}).get('name', ''),
                'info_en': i18n.get('en', {}).get('info', ''),
                'info_ro': i18n.get('ro', {}).get('info', ''),
                'info_ru': i18n.get('ru', {}).get('info', ''),
                'children_count': item.get('children', 0),
                'import_acts': item.get('import_acts', []),
                'export_acts': item.get('export_acts', []),
                'transit_acts': item.get('transit_acts', []),
                'valid_from': item.get('valid_from'),
                'valid_to': item.get('valid_to'),
            }

            flattened.append(flattened_item)

        # Sort by NC code for easier browsing
        flattened.sort(key=lambda x: x['nc'])

        logger.info(f"Built {len(flattened)} flattened items")
        return flattened

    def build_tree_structure(self, parent_id: Optional[int] = None) -> List[dict]:
        """Recursively build hierarchical tree structure"""
        children = self.children_by_parent.get(parent_id, [])
        tree = []

        for item in children:
            item_id = item['id']
            i18n = item.get('i18n', {})

            tree_item = {
                'id': item_id,
                'nc': item.get('nc', ''),
                'name_en': i18n.get('en', {}).get('name', ''),
                'name_ro': i18n.get('ro', {}).get('name', ''),
                'name_ru': i18n.get('ru', {}).get('name', ''),
                'info_en': i18n.get('en', {}).get('info', ''),
                'info_ro': i18n.get('ro', {}).get('info', ''),
                'info_ru': i18n.get('ru', {}).get('info', ''),
                'import_acts': item.get('import_acts', []),
                'export_acts': item.get('export_acts', []),
                'transit_acts': item.get('transit_acts', []),
            }

            # Recursively add children
            if item.get('children', 0) > 0:
                tree_item['children'] = self.build_tree_structure(item_id)

            tree.append(tree_item)

        # Sort by NC code (empty strings last, then alphanumeric)
        tree.sort(key=lambda x: (x['nc'] == '', x['nc']))
        return tree

    def save_outputs(self, flattened: List[dict], tree: List[dict]):
        """Save processed data to JSON files"""
        logger.info("Saving outputs...")

        # Save flattened structure
        flat_output = self.data_dir / OUTPUT_FILE
        with open(flat_output, 'w', encoding='utf-8') as f:
            json.dump(flattened, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved flattened data to {flat_output}")
        logger.info(f"File size: {flat_output.stat().st_size / 1024 / 1024:.2f} MB")

        # Save tree structure
        tree_output = self.data_dir / TREE_OUTPUT_FILE
        with open(tree_output, 'w', encoding='utf-8') as f:
            json.dump(tree, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved tree data to {tree_output}")
        logger.info(f"File size: {tree_output.stat().st_size / 1024 / 1024:.2f} MB")

    def generate_stats(self, items: List[dict]):
        """Generate and log statistics about the data"""
        logger.info("=" * 60)
        logger.info("Data Statistics:")
        logger.info(f"Total items: {len(items)}")

        # Count items with children
        with_children = sum(1 for item in items if item.get('children', 0) > 0)
        logger.info(f"Categories (with children): {with_children}")
        logger.info(f"Leaf items (no children): {len(items) - with_children}")

        # Count root level items
        root_items = sum(1 for item in items if item.get('parent') is None)
        logger.info(f"Root level categories: {root_items}")

        # Count items with acts
        with_import = sum(1 for item in items if item.get('import_acts'))
        with_export = sum(1 for item in items if item.get('export_acts'))
        with_transit = sum(1 for item in items if item.get('transit_acts'))
        logger.info(f"Items with import acts: {with_import}")
        logger.info(f"Items with export acts: {with_export}")
        logger.info(f"Items with transit acts: {with_transit}")

        # Max depth
        max_depth = max(len(self.get_parent_chain(item['id'])) for item in items)
        logger.info(f"Maximum hierarchy depth: {max_depth}")

        logger.info("=" * 60)

    def run(self):
        """Run the full processing pipeline"""
        logger.info("=" * 60)
        logger.info("Starting Moldova Tariff Nomenclature Processor")
        logger.info("=" * 60)

        try:
            # Load raw data
            items = self.load_raw_responses()
            if not items:
                logger.error("No items to process")
                return

            # Build lookup tables
            self.build_lookup_tables(items)

            # Generate statistics
            self.generate_stats(items)

            # Build flattened structure
            flattened = self.build_flattened_structure(items)

            # Build tree structure
            logger.info("Building tree structure...")
            tree = self.build_tree_structure(None)
            logger.info(f"Built tree with {len(tree)} root categories")

            # Save outputs
            self.save_outputs(flattened, tree)

            logger.info("=" * 60)
            logger.info("Processing completed successfully!")
            logger.info(f"Flattened data: {self.data_dir / OUTPUT_FILE}")
            logger.info(f"Tree data: {self.data_dir / TREE_OUTPUT_FILE}")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"Processing failed: {e}", exc_info=True)


if __name__ == "__main__":
    processor = NomenclatureProcessor()
    processor.run()
