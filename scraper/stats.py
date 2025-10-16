#!/usr/bin/env python3
"""
Quick statistics viewer for scraped data

Shows progress and data overview without re-processing.
"""

import json
from pathlib import Path
from collections import Counter


def main():
    print("=" * 70)
    print("Moldova Tariff Nomenclature - Data Statistics")
    print("=" * 70)

    # Check raw responses
    raw_dir = Path("raw_responses")
    if raw_dir.exists():
        raw_files = list(raw_dir.glob("*.json"))
        print(f"\n📥 Raw Responses: {len(raw_files)} files")

        # Count total items in raw files
        total_raw_items = 0
        for file in raw_files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    total_raw_items += len(data.get('results', []))
            except:
                pass
        print(f"   Total items in raw files: {total_raw_items}")
    else:
        print("\n📥 Raw Responses: Not found (run scraper.py first)")

    # Check processed data
    data_dir = Path("data")
    flat_file = data_dir / "nomenclature_flat.json"
    tree_file = data_dir / "nomenclature_tree.json"

    if flat_file.exists():
        with open(flat_file, 'r', encoding='utf-8') as f:
            items = json.load(f)

        print(f"\n📊 Processed Data (flat): {len(items)} items")

        # Category stats
        with_children = sum(1 for item in items if item.get('children_count', 0) > 0)
        leaf_items = len(items) - with_children
        print(f"   Categories (with children): {with_children}")
        print(f"   Leaf items (no children): {leaf_items}")

        # Root level
        root_items = sum(1 for item in items if item.get('parent_id') is None)
        print(f"   Root level categories: {root_items}")

        # Acts stats
        with_import = sum(1 for item in items if item.get('import_acts'))
        with_export = sum(1 for item in items if item.get('export_acts'))
        with_transit = sum(1 for item in items if item.get('transit_acts'))
        print(f"\n📋 Regulatory Acts:")
        print(f"   Items with import acts: {with_import}")
        print(f"   Items with export acts: {with_export}")
        print(f"   Items with transit acts: {with_transit}")

        # NC code distribution
        nc_lengths = Counter(len(item.get('nc', '')) for item in items if item.get('nc'))
        print(f"\n🏷️  NC Code Distribution:")
        for length in sorted(nc_lengths.keys()):
            print(f"   {length} digits: {nc_lengths[length]} items")

        # Max depth
        max_depth = max(len(item.get('parent_chain', [])) for item in items)
        print(f"\n📏 Hierarchy:")
        print(f"   Maximum depth: {max_depth} levels")

        # Depth distribution
        depth_dist = Counter(len(item.get('parent_chain', [])) for item in items)
        for depth in sorted(depth_dist.keys())[:5]:  # Show first 5 levels
            print(f"   Level {depth}: {depth_dist[depth]} items")

        # File size
        file_size = flat_file.stat().st_size / 1024 / 1024
        print(f"\n💾 File size: {file_size:.2f} MB")

        if tree_file.exists():
            tree_size = tree_file.stat().st_size / 1024 / 1024
            print(f"   Tree file: {tree_size:.2f} MB")

    else:
        print("\n📊 Processed Data: Not found (run processor.py first)")

    # Check logs
    logs_dir = Path("logs")
    if logs_dir.exists():
        log_files = list(logs_dir.glob("*.log"))
        print(f"\n📝 Logs: {len(log_files)} files")
    else:
        print("\n📝 Logs: None")

    print("\n" + "=" * 70)
    print("\nNext steps:")
    if not raw_dir.exists() or not raw_files:
        print("  1. Run: python scraper.py --dry-run")
        print("  2. Run: python scraper.py")
    elif not flat_file.exists():
        print("  1. Run: python processor.py")
    else:
        print("  ✓ Data ready! Try: python search.py <query>")
        print("  📖 See EXAMPLE_USAGE.md for AI-powered search examples")

    print("=" * 70)


if __name__ == "__main__":
    main()
