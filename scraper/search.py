#!/usr/bin/env python3
"""
Simple search utility for Moldova Tariff Nomenclature

Allows searching through the flattened nomenclature data by keywords.
Useful for quick lookups before using AI tools.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict

DATA_FILE = "data/nomenclature_flat.json"


def load_data() -> List[Dict]:
    """Load the flattened nomenclature data"""
    data_path = Path(DATA_FILE)

    if not data_path.exists():
        print(f"Error: {DATA_FILE} not found.")
        print("Run the scraper and processor first:")
        print("  1. python scraper.py")
        print("  2. python processor.py")
        sys.exit(1)

    with open(data_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def search(data: List[Dict], query: str, lang: str = 'en', limit: int = 10) -> List[Dict]:
    """
    Search for items matching the query

    Args:
        data: List of nomenclature items
        query: Search query (case-insensitive)
        lang: Language to search in ('en', 'ro', 'ru')
        limit: Maximum number of results to return

    Returns:
        List of matching items
    """
    query_lower = query.lower()
    results = []

    for item in data:
        # Search in name, path, and info fields for the specified language
        name = (item.get(f'name_{lang}') or '').lower()
        path = (item.get(f'path_{lang}') or '').lower()
        info = (item.get(f'info_{lang}') or '').lower()
        nc = (item.get('nc') or '').lower()

        # Check if query matches any field
        if (query_lower in name or
            query_lower in path or
            query_lower in info or
            query_lower in nc):
            results.append(item)

            if len(results) >= limit:
                break

    return results


def format_result(item: Dict, lang: str = 'en', show_acts: bool = False) -> str:
    """Format a single search result for display"""
    lines = []

    # Header with NC code and name
    nc = item.get('nc', 'N/A')
    name = item.get(f'name_{lang}', 'N/A')
    lines.append(f"\n{'='*80}")
    lines.append(f"NC Code: {nc}")
    lines.append(f"Name: {name}")

    # Path (breadcrumb)
    path = item.get(f'path_{lang}', '')
    if path and path != name:
        lines.append(f"Path: {path}")

    # Additional info
    info = item.get(f'info_{lang}', '')
    if info:
        lines.append(f"\nInfo: {info[:200]}{'...' if len(info) > 200 else ''}")

    # Children count
    children = item.get('children_count', 0)
    if children > 0:
        lines.append(f"Children: {children} subcategories")

    # Acts (if requested)
    if show_acts:
        import_acts = item.get('import_acts', [])
        export_acts = item.get('export_acts', [])
        transit_acts = item.get('transit_acts', [])

        if import_acts:
            lines.append(f"Import Acts: {len(import_acts)}")
        if export_acts:
            lines.append(f"Export Acts: {len(export_acts)}")
        if transit_acts:
            lines.append(f"Transit Acts: {len(transit_acts)}")

    return '\n'.join(lines)


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python search.py <query> [options]")
        print("\nOptions:")
        print("  --lang=en|ro|ru    Language to search (default: en)")
        print("  --limit=N          Max results to show (default: 10)")
        print("  --acts             Show regulatory acts info")
        print("\nExamples:")
        print("  python search.py \"wooden bed\"")
        print("  python search.py \"mobilă\" --lang=ro")
        print("  python search.py \"furniture\" --limit=20 --acts")
        sys.exit(1)

    # Parse arguments
    query = sys.argv[1]
    lang = 'en'
    limit = 10
    show_acts = False

    for arg in sys.argv[2:]:
        if arg.startswith('--lang='):
            lang = arg.split('=')[1]
        elif arg.startswith('--limit='):
            limit = int(arg.split('=')[1])
        elif arg == '--acts':
            show_acts = True

    # Validate language
    if lang not in ['en', 'ro', 'ru']:
        print(f"Error: Invalid language '{lang}'. Use 'en', 'ro', or 'ru'.")
        sys.exit(1)

    # Load data and search
    print(f"Loading data from {DATA_FILE}...")
    data = load_data()
    print(f"Loaded {len(data)} items")

    print(f"\nSearching for '{query}' in {lang.upper()}...")
    results = search(data, query, lang, limit)

    # Display results
    if not results:
        print("\nNo results found.")
        print("\nTips:")
        print("  - Try a different language (--lang=ro or --lang=ru)")
        print("  - Use broader search terms")
        print("  - Check spelling")
    else:
        print(f"\nFound {len(results)} result(s):")
        for item in results:
            print(format_result(item, lang, show_acts))

        if len(results) >= limit:
            print(f"\n{'='*80}")
            print(f"Showing first {limit} results. Use --limit=N to see more.")


if __name__ == "__main__":
    main()
