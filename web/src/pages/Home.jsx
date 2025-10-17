import { useState, useEffect, useMemo } from 'react'

function Home() {
  const [flatData, setFlatData] = useState([])
  const [filter, setFilter] = useState('')
  const [debouncedFilter, setDebouncedFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [toast, setToast] = useState({ show: false, message: '' })

  const normalizeText = (text) => {
    return text
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
  }

  const copyToClipboard = async (code) => {
    if (!code || code === '\u00A0') return

    try {
      await navigator.clipboard.writeText(code)
      setToast({ show: true, message: 'Copied to clipboard!' })
      setTimeout(() => setToast({ show: false, message: '' }), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  // Debounce filter input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedFilter(filter)
    }, 150)

    return () => clearTimeout(timer)
  }, [filter])

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
    if (!debouncedFilter.trim()) return flatData

    const searchTrimmed = debouncedFilter.trim()
    const isWildcard = searchTrimmed.endsWith('*')
    const searchValue = isWildcard ? searchTrimmed.slice(0, -1) : searchTrimmed
    const searchNormalized = normalizeText(searchValue)

    return flatData.filter(item => {
      const displayName = normalizeText(item.name_ro || item.name_ru || item.name_en)
      const displayCode = normalizeText(item.nc)

      // If wildcard search, only match NC codes that start with the pattern
      if (isWildcard) {
        return displayCode.startsWith(searchNormalized)
      }

      // Regular search - match anywhere in name or code
      return displayName.includes(searchNormalized) || displayCode.includes(searchNormalized)
    })
  }, [flatData, debouncedFilter])

  if (loading) {
    return (
      <div className="tree-container">
        <div className="loading">Loading nomenclature...</div>
      </div>
    )
  }

  return (
    <div className="tree-container">
      {toast.show && (
        <div className="toast">
          {toast.message}
        </div>
      )}

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
                <div className="tree-node-content">
                  <span
                    className="tree-code"
                    onClick={() => copyToClipboard(displayCode)}
                    title={displayCode ? 'Click to copy' : ''}
                    style={{ cursor: displayCode ? 'pointer' : 'default' }}
                  >
                    {displayCode || '\u00A0'}
                  </span>
                  <span
                    className="tree-name"
                    style={{ paddingLeft: `${item.level * 24}px` }}
                  >
                    {displayName}
                  </span>
                  {item.import_acts && item.import_acts.length > 0 && (
                    <span className="tree-badge">{item.import_acts.length} acts</span>
                  )}
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
