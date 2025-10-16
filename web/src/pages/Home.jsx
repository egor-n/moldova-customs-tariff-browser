import { useState, useEffect, useMemo } from 'react'
import { Link } from 'react-router-dom'

function Home() {
  const [flatData, setFlatData] = useState([])
  const [filter, setFilter] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/data/nomenclature_tree.json')
      .then(res => res.json())
      .then(data => {
        // Flatten the tree into a simple array with level info
        const flattened = []
        const flatten = (nodes, level = 0) => {
          nodes.forEach(node => {
            flattened.push({
              id: node.id,
              nc: node.nc || '',
              name_ro: node.name_ro || '',
              name_ru: node.name_ru || '',
              name_en: node.name_en || '',
              import_acts: node.import_acts || [],
              level
            })
            if (node.children && node.children.length > 0) {
              flatten(node.children, level + 1)
            }
          })
        }
        flatten(data)
        setFlatData(flattened)
        setLoading(false)
      })
      .catch(err => {
        console.error('Error loading data:', err)
        setLoading(false)
      })
  }, [])

  // Filter the flat list
  const filteredData = useMemo(() => {
    if (!filter.trim()) return flatData

    const searchLower = filter.toLowerCase().trim()
    return flatData.filter(item => {
      const displayName = (item.name_ro || item.name_ru || item.name_en).toLowerCase()
      const displayCode = item.nc.toLowerCase()
      return displayName.includes(searchLower) || displayCode.includes(searchLower)
    })
  }, [flatData, filter])

  if (loading) {
    return (
      <div className="tree-container">
        <div className="loading">Loading nomenclature...</div>
      </div>
    )
  }

  return (
    <div className="tree-container">
      <div className="tree-header">
        <input
          type="text"
          placeholder="Filter by NC code or name..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="tree-filter"
        />
        {filter && (
          <button
            className="clear-filter"
            onClick={() => setFilter('')}
          >
            Clear
          </button>
        )}
        <div className="tree-count">
          {filteredData.length.toLocaleString()} items
        </div>
      </div>

      <div className="tree-view">
        {filteredData.length > 0 ? (
          filteredData.map(item => {
            const displayName = item.name_ro || item.name_ru || item.name_en || 'Unnamed'
            const displayCode = item.nc

            return (
              <div key={item.id} className="tree-row">
                <div
                  className="tree-node-content"
                  style={{ paddingLeft: `${item.level * 24}px` }}
                >
                  <Link
                    to={`/category/${item.id}`}
                    className="tree-node-link"
                  >
                    {displayCode && <span className="tree-code">{displayCode}</span>}
                    <span className="tree-name">{displayName}</span>
                    {item.import_acts && item.import_acts.length > 0 && (
                      <span className="tree-badge">{item.import_acts.length} acts</span>
                    )}
                  </Link>
                </div>
              </div>
            )
          })
        ) : (
          <div className="no-items">No items found</div>
        )}
      </div>
    </div>
  )
}

export default Home
