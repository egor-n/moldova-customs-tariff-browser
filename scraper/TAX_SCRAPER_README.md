# Tax Information Scraper

## Quick Start

```bash
# Test with 3 codes first
python3 tax_scraper.py --dry-run

# Run full scrape (can be interrupted!)
python3 tax_scraper.py

# If interrupted, resume from last position
python3 tax_scraper.py --start-from 5000

# After scraping, merge with nomenclature data
python3 merge_tax_data.py
```

## What It Does

Fetches tax information (VAT, excise, customs duties) for all **12,661 unique NC codes** from the Moldova trade.gov.md API.

## Key Features

### 1. **Resume Capability**
- Automatically skips already-fetched files
- Can resume from any index with `--start-from`
- Never lose progress even if interrupted

### 2. **Robust Error Handling**
- Retries failed requests (3 attempts with backoff)
- Handles 404s (no tax data) gracefully
- Handles 429 rate limits with exponential backoff
- Comprehensive logging for debugging

### 3. **Progress Tracking**
- Real-time progress reports every 100 items
- Shows success/empty/error counts
- Logs saved to `logs/tax_scraper_*.log`

### 4. **Rate Limiting**
- 1-1.5 second delay between requests
- Respects API rate limits
- ~4.4 hours for complete scrape

## Output

### Raw Tax Responses
Location: `tax_responses/{nc_code}.json`

Each file contains the API response for one NC code:
```json
{
  "count": 1,
  "results": [{
    "vat": "20%",
    "excise": "-",
    "tax_values": [...],
    "i18n": {
      "ro": {...},
      "ru": {...},
      "en": {...}
    }
  }]
}
```

### Merged Data
After running `merge_tax_data.py`:

- `data/nomenclature_flat_with_tax.json` (14.7 MB)
- `data/nomenclature_tree_with_tax.json` (9.5 MB)

Each item gains a `tax_info` field:
```json
{
  "id": 61032,
  "nc": "0101",
  "name_ro": "Cai, măgari...",
  "tax_info": {
    "vat": "20%",
    "excise": "-",
    "tax_customs_ro": "...",
    "tax_values": [...]
  }
}
```

## Performance

- **Total codes**: 12,661
- **Rate**: ~1.25 seconds per request
- **Total time**: ~263 minutes (4.4 hours)
- **Resumable**: Yes, at any point
- **Retries**: 3 attempts per failed request

## Error Handling

The scraper handles:
- **404 Not Found**: Saves empty response, counts as successful
- **429 Rate Limit**: Waits with exponential backoff
- **Network errors**: Retries 3 times with backoff
- **Keyboard interrupt**: Saves progress, shows resume command

## Monitoring Progress

Watch the log file in real-time:
```bash
tail -f logs/tax_scraper_*.log
```

Progress reports show:
```
Progress: 1000/12661 (7.9%) - Success: 850, Empty: 100, Errors: 50
```

## Integration with Web App

After merging tax data, update the web app to use the enhanced JSON:

```javascript
// In web/src/pages/Home.jsx
fetch('/data/nomenclature_tree_with_tax.json')
  .then(res => res.json())
  .then(data => {
    // Each item now has tax_info field
    console.log(data[0].tax_info.vat) // "20%"
  })
```

## Troubleshooting

### Scraper stops/crashes
Resume from where it left off:
```bash
# Check logs for last successful index
tail logs/tax_scraper_*.log | grep Progress

# Resume from that index
python3 tax_scraper.py --start-from <index>
```

### Rate limiting (429 errors)
The scraper handles this automatically with exponential backoff. If persistent:
- Increase `MIN_DELAY` and `MAX_DELAY` in `tax_scraper.py`
- Current: 1.0-1.5 seconds

### Memory issues
Not likely (processes one at a time), but if needed:
- Run in smaller batches using `--start-from`
- Clear old log files from `logs/`

## Next Steps

1. Run `python3 tax_scraper.py` (start it and let it run)
2. After completion, run `python3 merge_tax_data.py`
3. Update web app to use `nomenclature_tree_with_tax.json`
4. Copy merged file to web app: `cp data/nomenclature_tree_with_tax.json ../web/public/data/`
