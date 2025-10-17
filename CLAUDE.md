# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a monorepo for Moldova's customs tariff nomenclature data:
- **Scraper** (Python): Fetches 15,067 tariff items from trade.gov.md API and processes them
- **Web App** (React): SPA for browsing the hierarchical nomenclature with advanced search

Data flows: API → scraper → processor → tree JSON → web app

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

# Scraping
python scraper.py --dry-run       # Test with first page only
python scraper.py                 # Full scrape (~12-15 min, 302 pages)

# Processing
python processor.py               # Process raw_responses/ → data/*.json

# Data sync to web app
cp data/nomenclature_tree.json ../web/public/data/

# Utilities
python search.py "keyword" --lang=ro --limit=10
python stats.py                   # View statistics
```

## Architecture

### Data Pipeline Architecture

The scraper and processor work together to transform flat API data into hierarchical structures:

1. **scraper.py**: Fetches paginated API responses (302 pages × 50 items)
   - Saves raw responses to `raw_responses/page_N.json`
   - Resume-safe: skips existing files
   - Rate-limited: 2-3 sec delays

2. **processor.py**: Transforms raw data into two formats
   - Builds lookup tables: `items_by_id` and `children_by_parent`
   - Generates `nomenclature_flat.json`: flat array with parent_chain and paths
   - Generates `nomenclature_tree.json`: nested hierarchy with children
   - **Critical**: Sorts tree at each level with `(nc == '', nc)` key to put NC codes first

3. **Web app consumes** `nomenclature_tree.json`:
   - Flattens on load (depth-first traversal)
   - All 15,067 items rendered with level-based indentation
   - No virtualization needed - modern browsers handle this efficiently

### Web App Architecture

**Home.jsx** is the main component - contains all search/display logic:

- **Data loading**: Fetches tree JSON, flattens with level tracking
- **Search features**:
  - Debounced input (150ms)
  - Diacritics-insensitive: `normalizeText()` uses NFD normalization + strip combining marks
  - Wildcard support: `*` suffix triggers `startsWith()` on NC codes only
  - Regular search: `includes()` on both names and codes
- **Display**: Maps over `filteredData` array, indents names only (NC codes stay left-aligned)
- **Clipboard**: Click NC codes to copy with toast notification

**Key patterns**:
- NC codes always render (use `\u00A0` for empty to maintain spacing)
- Toast state managed locally with setTimeout cleanup
- Filter operates on flattened data (not tree traversal during search)

## Data Format

### Tree JSON (web/public/data/nomenclature_tree.json)
```json
[
  {
    "id": 61032,
    "nc": "0101",
    "name_en": "...", "name_ro": "...", "name_ru": "...",
    "import_acts": [...],
    "children": [...]
  }
]
```

**Ordering invariant**: At each level, items with NC codes appear first (sorted), then items without NC codes (category headers). This is enforced in `processor.py:196` with sort key `(x['nc'] == '', x['nc'])`.

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
- Serves 9.5MB tree JSON with cache headers
- SPA redirects configured for client-side routing

## Data Statistics

- Total items: 15,067
- Root categories: 1,262
- Leaf items: 9,889
- Hierarchy depth: 9 levels
- Items with import acts: 3,520+

## Common Workflows

### Updating Data After API Changes
```bash
cd scraper
python scraper.py              # Re-scrape (will skip existing if resuming)
python processor.py            # Regenerate tree JSON
cp data/nomenclature_tree.json ../web/public/data/
cd ../web
npm run dev                    # Test changes
```

### Adding New Search Features
Modify `web/src/pages/Home.jsx`:
- Search logic is in the `filteredData` useMemo
- All filtering happens on the flattened array (not recursive tree traversal)
- Keep debouncing (150ms) for performance with 15k items
