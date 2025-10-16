# Moldova Tariff Nomenclature Scraping Plan

## Overview
Scraping hierarchical tariff/tax data from Moldova's trade.gov.md API for AI-powered category search.

## API Details
- **Base URL**: `https://trade.gov.md/api/tarim-nomenclature/`
- **Total records**: ~15,067 items
- **Structure**: Hierarchical parent-child relationships
- **Pagination**: `page` and `page_size` parameters (max 1000/page)

## Data Structure
Each record contains:
- `id`, `parent`, `nc` (nomenclature code)
- `i18n`: Multilingual names (ru, ro, en) with `name` and `info` fields
- `children`: Count of child categories
- `import_acts`, `export_acts`, `transit_acts`: Regulatory information
- `valid_from`, `valid_to`: Validity timestamps

## Scraping Strategy

### Stage 1: Data Collection (with safety net)
1. Save each API response as-is to `raw_responses/page_{n}.json`
2. Never re-fetch existing files (check before each request)
3. Fetch all pages sequentially:
   - API returns ALL 15,067 items across 302 pages (no recursion needed!)
   - Items include `parent` field for hierarchy relationships
   - Pagination with 50 items per page

### Stage 2: Data Processing
1. Parse all raw JSON files
2. Build flattened JSON structure with full path/breadcrumb trails
3. Output: `nomenclature_flat.json` - single array optimized for AI search

Example processed structure:
```json
[
  {
    "id": 69000,
    "nc": "530310000",
    "path": "Chapter 53 > Other vegetable textile fibres > Jute",
    "name_en": "Jute and other textile bast fibres, raw or retted",
    "name_ro": "Iută şi alte fibre textile liberiene...",
    "name_ru": "...",
    "parent_chain": [61032, 68999, 69000],
    "children_count": 0,
    "import_acts": [...],
    "export_acts": [...],
    "transit_acts": [...]
  }
]
```

## Rate Limiting & Safety
- Minimum 2-3 seconds between requests
- Exponential backoff on errors (429, 5xx)
- Respect any rate limit responses
- Resume capability (skip existing files)
- Progress tracking and logging

## Folder Structure
```
/raw_responses/       # All API responses (never delete)
/data/                # Processed data
  - nomenclature_flat.json
/logs/                # Scraping logs
/scripts/             # Scraper and processor scripts
```

## Use Case
AI-powered search for finding correct tariff codes.
Example: "wooden children's bed" → search across names/paths in flat JSON → get NC code

## Implementation Notes
- Python with `requests` library
- Session management for connection pooling
- Dry-run mode to estimate scope before full scrape
- Error logging for debugging
