# Moldova Tariff Nomenclature Scraper

Scrapes hierarchical tariff/tax data from Moldova's trade.gov.md API for AI-powered search and analysis.

## Overview

This project provides tools to:
1. **Scrape** all tariff nomenclature data from Moldova's trade API (15,067 items)
2. **Process** raw data into structured formats with hierarchical paths
3. **Search** through the data using keywords or AI tools

**Note**: The API returns ALL items in a flat paginated list with parent/child relationships as metadata. No recursive fetching needed!

## Quick Start

### 1. Install dependencies
```bash
cd scraper
pip install -r requirements.txt
```

### 2. Test the scraper (dry run)
```bash
python scraper.py --dry-run
```

This fetches only the first page to show scope (15,067 total items across ~302 pages).

### 3. Run the full scraper
```bash
python scraper.py
```

**Estimated time**: ~12-15 minutes (302 pages × 2.5 sec/page)

The scraper will:
- Fetch all pages sequentially (no recursion needed - API returns everything)
- Save each page to `raw_responses/page_{N}.json`
- Skip existing files (safe to interrupt and resume)
- Add 2-3 second delays between requests
- Log all activity to `logs/`

### 4. Process the raw data
```bash
python processor.py
```

This creates:
- `data/nomenclature_flat.json`: Flattened array with full hierarchical paths
- `data/nomenclature_tree.json`: Nested tree structure
- Statistics and logs

### 5. Search the data
```bash
# Basic search
python search.py "furniture"

# Search in Romanian
python search.py "mobilă" --lang=ro

# Show more results with regulatory acts
python search.py "textile" --limit=20 --acts
```

## Project Structure

```
├── scraper/             # Python scraper and tools
│   ├── scraper.py       # API scraper (sequential, rate-limited)
│   ├── processor.py     # Data processor (builds structured outputs)
│   ├── search.py        # Simple keyword search utility
│   ├── stats.py         # Statistics viewer
│   ├── PLAN.md          # Detailed implementation plan
│   ├── EXAMPLE_USAGE.md # AI-powered search examples
│   ├── requirements.txt # Python dependencies
│   ├── raw_responses/   # Raw API responses (gitignored)
│   ├── data/            # Processed data (gitignored)
│   └── logs/            # Scraping logs (gitignored)
└── README.md            # This file
```

## Features

### Scraper
- **Resume capability**: Skips already-downloaded files
- **Rate limiting**: 2-3 seconds between requests with exponential backoff
- **Safety net**: All raw responses saved individually (never lost)
- **Progress tracking**: Detailed logging to console and file
- **Error handling**: Retries with exponential backoff on network errors

### Processor
- **Hierarchical paths**: Full breadcrumb trails for each item
- **Parent chains**: Complete ancestry for tree navigation
- **Multilingual**: Preserves all languages (EN, RO, RU)
- **Regulatory info**: Import/export/transit acts included
- **Statistics**: Depth analysis, act counts, etc.

### Search
- **Keyword search**: Search by name, path, info, or NC code
- **Multilingual**: Search in English, Romanian, or Russian
- **Flexible**: Adjustable result limits
- **AI-ready**: Data optimized for embedding-based search

## Data Format

### Flattened JSON Structure
```json
{
  "id": 61034,
  "nc": "010121000",
  "parent_id": 61033,
  "parent_chain": [61032, 61033, 61034],
  "path_en": "Horses, asses, mules and hinnies, live: > – Horses: > – – Pure-bred breeding animals",
  "path_ro": "...",
  "path_ru": "...",
  "name_en": "– – Pure-bred breeding animals",
  "name_ro": "...",
  "name_ru": "...",
  "info_en": "Operations for import, export and transit...",
  "children_count": 0,
  "import_acts": [...],
  "export_acts": [...],
  "transit_acts": [...]
}
```

## Use Cases

### AI-Powered Search
Load `data/nomenclature_flat.json` into your AI tool:
- **Semantic search**: "wooden children's bed" → find correct tariff code
- **Classification**: Automatically categorize products
- **Compliance**: Check import/export requirements

### Data Analysis
- Analyze tariff structure and hierarchy
- Compare regulatory requirements across categories
- Generate reports on product classifications

## API Information

- **Base URL**: `https://trade.gov.md/api/tarim-nomenclature/`
- **Total items**: 15,067
- **Pages**: 302 (50 items per page)
- **Hierarchy depth**: Up to 9 levels
- **Data structure**: Flat list with parent/child relationships in metadata
- **Rate limits**: None specified (we use 2-3 sec delays to be respectful)

## Notes

- The API returns ALL items without needing recursive category fetching
- The `parent` field creates the hierarchy - processor builds the tree structure
- The scraper is designed to be interrupted (Ctrl+C) and resumed safely
- All raw responses are preserved for auditing and re-processing
- The data includes regulatory acts and multilingual descriptions
- Maximum hierarchy depth: 9 levels
- Root categories: 1,262 items (items without a parent)

## Troubleshooting

**"No JSON files found"**: Run `scraper.py` first to download data

**Rate limited (429)**: The scraper handles this automatically with exponential backoff

**Incomplete scrape**: Just re-run `scraper.py` - it will skip existing files and continue

**Search returns nothing**: Try a different language with `--lang=ro` or broader terms
