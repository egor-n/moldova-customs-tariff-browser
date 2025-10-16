import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import Fuse from 'fuse.js'

function Home() {
  const [data, setData] = useState([])
  const [searchQuery, setSearchQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(true)
  const [fuse, setFuse] = useState(null)

  useEffect(() => {
    // Load the data
    fetch('/data/nomenclature_flat.json')
      .then(res => res.json())
      .then(data => {
        setData(data)

        // Initialize Fuse.js for fuzzy search
        const fuseInstance = new Fuse(data, {
          keys: [
            { name: 'nc_code', weight: 2 },
            { name: 'name_ro', weight: 1.5 },
            { name: 'name_ru', weight: 1.5 },
            { name: 'name_en', weight: 1 },
            { name: 'path', weight: 0.5 }
          ],
          threshold: 0.4,
          includeScore: true,
          minMatchCharLength: 2
        })

        setFuse(fuseInstance)
        setLoading(false)
      })
      .catch(err => {
        console.error('Error loading data:', err)
        setLoading(false)
      })
  }, [])

  useEffect(() => {
    if (!fuse || !searchQuery.trim()) {
      setResults([])
      return
    }

    // Perform fuzzy search
    const searchResults = fuse.search(searchQuery)
    setResults(searchResults.slice(0, 50)) // Limit to 50 results
  }, [searchQuery, fuse])

  const handleSearch = (e) => {
    setSearchQuery(e.target.value)
  }

  if (loading) {
    return (
      <div className="container">
        <div className="loading">Loading data...</div>
      </div>
    )
  }

  return (
    <div className="container">
      <div className="search-page">
        <div className="search-header">
          <h2>Moldova Customs Tariff Database</h2>
          <p>Search by NC code, name in any language, or keywords</p>
        </div>

        <div className="search-box">
          <input
            type="text"
            placeholder="Enter NC code or search terms..."
            value={searchQuery}
            onChange={handleSearch}
            className="search-input"
            autoFocus
          />
        </div>

        {searchQuery.trim() && (
          <div className="search-results">
            <div className="results-header">
              <h3>
                {results.length > 0
                  ? `Found ${results.length} result${results.length !== 1 ? 's' : ''}`
                  : 'No results found'
                }
              </h3>
            </div>

            <div className="results-list">
              {results.map(({ item, score }) => (
                <Link
                  key={item.id}
                  to={`/category/${item.id}`}
                  className="result-card"
                >
                  <div className="result-header">
                    <span className="nc-code">{item.nc_code}</span>
                    {item.is_leaf && <span className="badge">Leaf</span>}
                  </div>
                  <div className="result-content">
                    <h4>{item.name_ro || item.name_ru || item.name_en}</h4>
                    {item.path && (
                      <p className="result-path">{item.path}</p>
                    )}
                  </div>
                  {item.import_acts && item.import_acts.length > 0 && (
                    <div className="result-meta">
                      {item.import_acts.length} regulatory act{item.import_acts.length !== 1 ? 's' : ''}
                    </div>
                  )}
                </Link>
              ))}
            </div>
          </div>
        )}

        {!searchQuery.trim() && (
          <div className="search-tips">
            <h3>Search Tips</h3>
            <ul>
              <li>Search by NC code (e.g., "0101")</li>
              <li>Search by product name in Romanian, Russian, or English</li>
              <li>Use keywords related to the product category</li>
              <li>Partial matches and typos are handled automatically</li>
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}

export default Home
