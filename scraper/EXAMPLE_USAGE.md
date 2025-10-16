# Example Usage: AI-Powered Tariff Search

## Use Case: Finding the Correct Tariff Code

Let's say you want to import a "wooden children's bed" to Moldova and need to find the correct tariff classification code.

## Method 1: Simple Keyword Search

```bash
# Search for furniture-related terms
python search.py "furniture" --limit=10

# Search for wooden items
python search.py "wood" --limit=10

# Search for beds
python search.py "bed" --limit=10

# Try in Romanian
python search.py "mobilă" --lang=ro --limit=10
python search.py "lemn" --lang=ro --limit=10
```

## Method 2: AI-Powered Semantic Search

Load the flattened JSON into your favorite AI tool (ChatGPT, Claude, etc.):

### Example with Claude Code

1. Load the data:
```python
import json

with open('data/nomenclature_flat.json', 'r', encoding='utf-8') as f:
    nomenclature = json.load(f)
```

2. Ask AI to find relevant categories:
```
User: "I need to find the tariff code for a wooden children's bed.
Search through this nomenclature data and find the most appropriate category."

[Paste or provide the JSON data]
```

3. The AI will search semantically through:
   - `name_en`, `name_ro`, `name_ru`: Product names
   - `path_en`, `path_ro`, `path_ru`: Full hierarchical paths
   - `info_en`, `info_ro`, `info_ru`: Additional descriptions
   - `nc`: Nomenclature codes

### Example with Embeddings

For large-scale searches, create embeddings:

```python
from sentence_transformers import SentenceTransformer
import numpy as np

# Load model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Create searchable text for each item
def create_search_text(item):
    parts = [
        item.get('nc', ''),
        item.get('name_en', ''),
        item.get('path_en', ''),
        item.get('info_en', '')[:200]  # First 200 chars of info
    ]
    return ' | '.join(filter(None, parts))

# Build search index
search_texts = [create_search_text(item) for item in nomenclature]
embeddings = model.encode(search_texts)

# Search function
def semantic_search(query, top_k=5):
    query_embedding = model.encode([query])
    scores = np.dot(embeddings, query_embedding.T).flatten()
    top_indices = np.argsort(scores)[-top_k:][::-1]

    results = []
    for idx in top_indices:
        item = nomenclature[idx]
        results.append({
            'score': scores[idx],
            'nc': item['nc'],
            'name': item['name_en'],
            'path': item['path_en']
        })
    return results

# Search
results = semantic_search("wooden children's bed")
for r in results:
    print(f"Score: {r['score']:.3f} | NC: {r['nc']} | {r['name']}")
```

## Method 3: Direct JSON Inspection

Open `data/nomenclature_flat.json` and browse:

```json
[
  {
    "id": 61034,
    "nc": "010121000",
    "parent_chain": [61032, 61033, 61034],
    "path_en": "Horses, asses, mules > Horses > Pure-bred",
    "name_en": "Pure-bred breeding animals",
    "children_count": 0,
    "import_acts": [{"id": 100, "act_cod": "027"}]
  },
  ...
]
```

Filter by:
- `children_count: 0` → Leaf nodes (most specific categories)
- `import_acts` → Items with import regulations
- `nc` length → More digits = more specific

## Understanding the Results

### NC Code Structure
- **4 digits**: Chapter (e.g., "0101" = Horses)
- **6 digits**: Heading (e.g., "010121" = Pure-bred horses)
- **8+ digits**: Subheading (e.g., "010121000" = Specific type)

### Hierarchical Path
Shows the full classification tree:
```
Chapter 94 > Furniture > Bedroom furniture > Beds > Wooden beds > Children's beds
```

### Regulatory Acts
- `import_acts`: Required for importing this category
- `export_acts`: Required for exporting
- `transit_acts`: Required for transit through Moldova

## Tips for Better Results

1. **Use broader terms first**: Start with "furniture" before "antique mahogany dresser"

2. **Check multiple languages**: Some items have better descriptions in Romanian
   ```bash
   python search.py "lemn" --lang=ro  # "wood" in Romanian
   ```

3. **Follow the hierarchy**: If you find a parent category, look at its children
   - Check `parent_chain` to understand ancestry
   - Items with `children_count > 0` are not the final classification

4. **Verify with official sources**: Always cross-reference with Moldova customs or trade officials

## Real-World Workflow

1. **Initial search** → Find broad category
2. **Narrow down** → Follow hierarchy to more specific subcategories
3. **Verify** → Check `info` field for special requirements
4. **Check acts** → Review required import/export permits
5. **Confirm** → Contact customs with the NC code you found

## Example: Full Search Process

```bash
# Step 1: Start broad
python search.py "furniture" --limit=20

# Step 2: Found chapter 94 (Furniture), now search within it
python search.py "94" --limit=50

# Step 3: Found beds, search more specifically
python search.py "bed" --limit=10

# Step 4: Check for wooden items
python search.py "wood bed" --limit=5

# Step 5: Review acts and regulations
python search.py "9403" --acts
```

## Next Steps

After finding your code:
1. Note the full NC code (e.g., "9403.50.10")
2. Check `import_acts` for required documentation
3. Review `info` field for special conditions
4. Contact Moldova customs with this code to confirm
5. Prepare necessary certificates/permits based on acts

## Advanced: Build Your Own Interface

Create a web app or chatbot:
- Load `nomenclature_flat.json` into your backend
- Use AI/embeddings for search
- Display results with full paths and regulatory info
- Allow users to drill down through hierarchy
- Link to external resources for each act_cod
