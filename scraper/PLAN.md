# Moldova Tariff Nomenclature Scraping Plan

## Overview
Scraping hierarchical tariff/tax data from Moldova's trade.gov.md API for AI-powered category search.

## API Endpoints
1. **Nomenclature API**: `https://trade.gov.md/api/tarim-nomenclature/`
   - **Total records**: ~15,067 items
   - **Structure**: Hierarchical parent-child relationships
   - **Pagination**: `page` and `page_size` parameters (max 1000/page)

2. **Tax API**: `https://trade.gov.md/api/tarim_tax/`
   - **Query param**: `tarim__nc` (NC code)
   - **Returns**: VAT, excise, customs tax info per NC code
   - **Total requests**: ~12,661 unique NC codes

## Data Structure
Each record contains:
- `id`, `parent`, `nc` (nomenclature code)
- `i18n`: Multilingual names (ru, ro, en) with `name` and `info` fields
- `children`: Count of child categories
- `import_acts`, `export_acts`, `transit_acts`: Regulatory information
- `valid_from`, `valid_to`: Validity timestamps

## Scraping Strategy

### Stage 1: Nomenclature Collection
**Script**: `scraper.py`

1. Save each API response as-is to `raw_responses/page_{n}.json`
2. Never re-fetch existing files (check before each request)
3. Fetch all pages sequentially:
   - API returns ALL 15,067 items across 302 pages (no recursion needed!)
   - Items include `parent` field for hierarchy relationships
   - Pagination with 50 items per page

**Usage**:
```bash
# Dry run to test
python scraper.py --dry-run

# Full scrape (~12-15 minutes)
python scraper.py
```

### Stage 2: Tax Information Collection
**Script**: `tax_scraper.py`

1. Load all unique NC codes from processed data
2. Fetch tax info for each NC code from `/api/tarim_tax/`
3. Save each response to `tax_responses/{nc_code}.json`
4. Resume capability - skips existing files
5. Rate limiting: 1-1.5s between requests

**Usage**:
```bash
# Dry run with first 3 codes
python tax_scraper.py --dry-run

# Full scrape (~263 minutes = 4.4 hours for 12,661 codes)
python tax_scraper.py

# Resume from specific index if interrupted
python tax_scraper.py --start-from 1000
```

### Stage 3: Data Processing
**Script**: `processor.py`

1. Parse all raw JSON files from `raw_responses/`
2. Build flattened JSON structure with full path/breadcrumb trails
3. Build tree structure for hierarchical display
4. Output files:
   - `nomenclature_flat.json` - single array optimized for AI search
   - `nomenclature_tree.json` - hierarchical structure

**Usage**:
```bash
python processor.py
```

### Stage 4: Tax Data Merging
**Script**: `merge_tax_data.py`

1. Load all tax responses from `tax_responses/`
2. Merge tax data with nomenclature by NC code
3. Add `tax_info` field to each item
4. Output files:
   - `nomenclature_flat_with_tax.json` - flat structure with tax data
   - `nomenclature_tree_with_tax.json` - tree structure with tax data

**Usage**:
```bash
python merge_tax_data.py
```

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
/raw_responses/       # Nomenclature API responses (never delete)
  - page_1.json, page_2.json, ...
/tax_responses/       # Tax API responses (never delete)
  - 0101.json, 010121000.json, ...
/data/                # Processed data
  - nomenclature_flat.json           # Base flat structure
  - nomenclature_tree.json           # Base tree structure
  - nomenclature_flat_with_tax.json  # With tax info merged
  - nomenclature_tree_with_tax.json  # With tax info merged
/logs/                # Scraping and processing logs
  - scraper_*.log
  - tax_scraper_*.log
  - processor_*.log
  - merge_tax_*.log
```

## Complete Workflow

To collect all data from scratch:

```bash
# 1. Scrape nomenclature (12-15 minutes)
python scraper.py

# 2. Process nomenclature into flat/tree structures
python processor.py

# 3. Scrape tax information for all NC codes (~4.4 hours)
# This can be interrupted and resumed!
python tax_scraper.py

# If interrupted, resume with:
# python tax_scraper.py --start-from <last_index>

# 4. Merge tax data with nomenclature
python merge_tax_data.py
```

Final outputs:
- `data/nomenclature_flat_with_tax.json` (14.7 MB)
- `data/nomenclature_tree_with_tax.json` (9.5 MB)

## Use Case
AI-powered search for finding correct tariff codes.
Example: "wooden children's bed" → search across names/paths in flat JSON → get NC code

## Implementation Notes
- Python with `requests` library
- Session management for connection pooling
- Dry-run mode to estimate scope before full scrape
- Error logging for debugging
