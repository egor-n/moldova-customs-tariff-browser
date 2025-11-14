# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a monorepo for Moldova's customs tariff nomenclature data:
- **Scraper** (Python): Fetches 15,067 tariff items from trade.gov.md API and processes them
- **Tax Scraper** (Python): Fetches VAT, customs duties, and excise tax data for 12,661 NC codes
- **Web App** (React): SPA for browsing the hierarchical nomenclature with advanced search and tax information

Data flows: API → scraper → processor → tree JSON → tax scraper → merger → enhanced tree JSON → web app

## Development Commands

### Web App (Primary Interface)
```bash
cd web
npm install              # Install dependencies
npm run dev             # Start dev server (http://localhost:5173)
npm run build           # Build for production (outputs to dist/)
npm run lint            # Run ESLint
```

### Scraper (Data Collection)
```bash
cd scraper
pip install -r requirements.txt   # Install dependencies

# Scraping nomenclature
python scraper.py --dry-run       # Test with first page only
python scraper.py                 # Full scrape (~12-15 min, 302 pages)

# Processing nomenclature
python processor.py               # Process raw_responses/ → data/*.json

# Scraping tax data
python tax_scraper.py --dry-run   # Test with first 3 NC codes
python tax_scraper.py             # Full scrape (~4.4 hours, 12,661 codes)
python tax_scraper.py --start-from 5000  # Resume from specific index

# Merging tax data with nomenclature
python merge_tax_data.py          # Creates *_with_tax.json files

# Data sync to web app
cp data/nomenclature_tree_with_tax.json ../web/public/data/

# Utilities
python search.py "keyword" --lang=ro --limit=10
python stats.py                   # View statistics
```

## Architecture

### Data Pipeline Architecture

The scraper, processor, tax scraper, and merger work together to create an enhanced hierarchical dataset:

1. **scraper.py**: Fetches paginated API responses (302 pages × 50 items)
   - Saves raw responses to `raw_responses/page_N.json`
   - Resume-safe: skips existing files
   - Rate-limited: 2-3 sec delays

2. **processor.py**: Transforms raw data into two formats
   - Builds lookup tables: `items_by_id` and `children_by_parent`
   - Generates `nomenclature_flat.json`: flat array with parent_chain and paths
   - Generates `nomenclature_tree.json`: nested hierarchy with children
   - **Critical**: Sorts tree at each level with `(nc == '', nc)` key to put NC codes first

3. **tax_scraper.py**: Fetches tax information for each NC code
   - Fetches VAT, customs duties (by country), and excise tax
   - Saves individual responses to `tax_responses/{nc_code}.json`
   - Resume-safe: can start from any index with `--start-from`
   - Rate-limited: 1-1.5 sec delays
   - Total: 12,661 unique NC codes (~4.4 hours)

4. **merge_tax_data.py**: Combines nomenclature with tax data
   - Reads nomenclature tree and tax responses
   - Adds `tax_info` field to each item with an NC code
   - Generates `nomenclature_tree_with_tax.json` and `nomenclature_flat_with_tax.json`
   - Preserves tree structure and ordering

5. **Web app consumes** `nomenclature_tree_with_tax.json`:
   - Flattens on load (depth-first traversal)
   - All 15,067 items rendered with level-based indentation
   - Displays tax columns: VAT, Customs (by country), Excise
   - Uses react-window for virtualized rendering of large lists

### Web App Architecture

**Home.jsx** is the main component - contains all search/display logic:

- **Data loading**: Fetches `nomenclature_tree_with_tax.json`, flattens with level tracking and tax info
- **Search features**:
  - Debounced input (150ms)
  - Diacritics-insensitive: `normalizeText()` uses NFD normalization + strip combining marks
  - **Wildcard**: `*` suffix triggers `startsWith()` on NC codes only
  - **Exact match**: Wrap in quotes `"text"` for exact phrase matching
  - **Multi-word**: All words must be present in at least one name field
  - **Numeric**: Automatic NC code search with space/dot tolerance
  - **Context-aware**: Shows matched items with all parents and children
  - **Highlighting**: Matched terms highlighted with `<mark>` tags
- **Tax display**: Table layout with VAT, Customs (by country), and Excise columns
- **Country selector**: Dropdown to choose country for customs rate display (60+ countries)
- **Display**: Uses react-window's `List` component for virtualized rendering
- **Clipboard**: Click NC codes to copy with toast notification
- **LLM export**: Download button generates hierarchical markdown for LLM use
- **ChatGPT integration**: Button opens ChatGPT with helper prompt for AI-assisted classification

**Key patterns**:
- NC codes always render (use `\u00A0` for empty to maintain spacing)
- Toast state managed locally with setTimeout cleanup
- Filter operates on flattened data (not tree traversal during search)
- Tax info extracted during flattening: `vat`, `excise`, `tax_values` array
- Country-specific customs rates looked up from `tax_values` array by country ID
- Virtualized rendering with `react-window` for performance with 15k+ items

## Data Format

### Tree JSON (web/public/data/nomenclature_tree_with_tax.json)
```json
[
  {
    "id": 61032,
    "nc": "0101",
    "name_en": "...", "name_ro": "...", "name_ru": "...",
    "import_acts": [...],
    "tax_info": {
      "vat": "20%",
      "excise": "-",
      "tax_values": [
        {"country": 1, "tax_value": "0%"},
        {"country": 2, "tax_value": "5%"}
      ]
    },
    "children": [...]
  }
]
```

**Ordering invariant**: At each level, items with NC codes appear first (sorted), then items without NC codes (category headers). This is enforced in `processor.py:196` with sort key `(x['nc'] == '', x['nc'])`.

**Tax info structure**:
- `vat`: VAT rate as string (e.g., "20%", "-")
- `excise`: Excise tax as string (e.g., "-", "5%")
- `tax_values`: Array of country-specific customs rates
  - Each entry has `country` (integer ID) and `tax_value` (string percentage)
  - Country IDs mapped to names in `web/src/config/countries.js`

### API Response Format
Raw API returns flat list with parent/child metadata:
```json
{
  "id": 61034,
  "nc": "010121000",
  "parent": 61033,
  "children": 0,
  "i18n": {
    "en": {"name": "...", "info": "..."},
    "ro": {"name": "...", "info": "..."},
    "ru": {"name": "...", "info": "..."}
  },
  "import_acts": [...],
  "export_acts": [...],
  "transit_acts": [...]
}
```

## Important Patterns

### Processor Sorting Logic
When modifying `processor.py`, preserve the tree ordering:
```python
tree.sort(key=lambda x: (x['nc'] == '', x['nc']))
```
This ensures NC codes (e.g., "0101") appear before empty strings (category headers).

### Search Normalization
The web app's `normalizeText()` function must preserve this pattern:
```javascript
.toLowerCase()
.normalize('NFD')              // Decompose diacritics
.replace(/[\u0300-\u036f]/g, '') // Remove combining marks
```

### NC Code Space Reservation
Always render NC code span even when empty to maintain alignment:
```javascript
<span className="tree-code">{displayCode || '\u00A0'}</span>
```

## Deployment

Web app configured for Netlify via `netlify.toml`:
- Build: `npm run build` (outputs to `dist/`)
- Serves enhanced tree JSON with tax data and cache headers
- SPA redirects configured for client-side routing

## Data Statistics

- Total items: 15,067
- Unique NC codes: 12,661 (with tax information)
- Root categories: 1,262
- Leaf items: 9,889
- Hierarchy depth: 9 levels
- Items with import acts: 3,520+
- Countries supported: 60+ (for customs rates)

## Common Workflows

### Updating Data After API Changes
```bash
cd scraper
python scraper.py                              # Re-scrape nomenclature (will skip existing)
python processor.py                            # Regenerate tree JSON
python tax_scraper.py                          # Re-scrape tax data (resumable)
python merge_tax_data.py                       # Merge tax info into tree
cp data/nomenclature_tree_with_tax.json ../web/public/data/
cd ../web
npm run dev                                    # Test changes
```

### Adding Tax Data to Existing Nomenclature
```bash
cd scraper
# Assuming you already have nomenclature_tree.json
python tax_scraper.py                          # Scrape tax data (~4.4 hours)
python merge_tax_data.py                       # Merge into existing tree
cp data/nomenclature_tree_with_tax.json ../web/public/data/
```

### Resuming Interrupted Tax Scraper
```bash
cd scraper
tail logs/tax_scraper_*.log | grep Progress    # Check last successful index
python tax_scraper.py --start-from 5000        # Resume from that index
```

### Adding New Search Features
Modify `web/src/pages/Home.jsx`:
- Search logic is in the `filteredData` useMemo
- All filtering happens on the flattened array (not recursive tree traversal)
- Keep debouncing (150ms) for performance with 15k items
- Use `includeParentsAndChildren()` helper to show context around matches
- Use `highlightText()` helper to highlight matched terms in results
