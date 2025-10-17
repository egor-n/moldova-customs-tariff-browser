import { useState, useEffect, useMemo } from 'react'
import { List } from 'react-window'
import Fuse from 'fuse.js'

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
    fetch('/data/nomenclature_tree_with_tax.json')
      .then(res => res.json())
      .then(data => {
        // Flatten the tree into a simple array with level info
        const flattened = []
        const flatten = (nodes, level = 0) => {
          nodes.forEach(node => {
            const taxInfo = node.tax_info || {}
            flattened.push({
              id: node.id,
              nc: node.nc || '',
              name_ro: node.name_ro || '',
              name_ru: node.name_ru || '',
              name_en: node.name_en || '',
              import_acts: node.import_acts || [],
              level,
              // Tax information
              vat: taxInfo.vat || '',
              excise: taxInfo.excise || '',
              tax_values: taxInfo.tax_values || []
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

  // Initialize Fuse.js for fuzzy search
  const fuse = useMemo(() => {
    return new Fuse(flatData, {
      keys: [
        { name: 'name_ro', weight: 0.4 },
        { name: 'name_ru', weight: 0.3 },
        { name: 'name_en', weight: 0.2 },
        { name: 'nc', weight: 0.1 }
      ],
      threshold: 0.3,        // 0 = exact, 1 = match anything (0.3 = moderate fuzziness)
      distance: 100,         // Max distance from start for typo
      ignoreLocation: true,  // Match anywhere in string
      minMatchCharLength: 2  // Minimum characters to trigger match
    })
  }, [flatData])

  // Filter the flat list with fuzzy search
  const filteredData = useMemo(() => {
    if (!debouncedFilter.trim()) return flatData

    const searchTrimmed = debouncedFilter.trim()
    const isWildcard = searchTrimmed.endsWith('*')
    const searchValue = isWildcard ? searchTrimmed.slice(0, -1) : searchTrimmed

    // Wildcard search - exact prefix match on NC codes
    if (isWildcard) {
      const searchNormalized = normalizeText(searchValue)
      return flatData.filter(item => {
        const displayCode = normalizeText(item.nc)
        return displayCode.startsWith(searchNormalized)
      })
    }

    // Fuzzy search
    const results = fuse.search(searchValue)
    return results.map(result => result.item)
  }, [flatData, debouncedFilter, fuse])

  // Helper to get primary customs rate
  const getPrimaryCustomsRate = (taxValues) => {
    if (!taxValues || taxValues.length === 0) return '-'
    // Find first non-empty rate
    const nonEmpty = taxValues.find(tv => tv.tax_value && tv.tax_value.trim())
    return nonEmpty ? nonEmpty.tax_value : '-'
  }

  // Helper to format customs tooltip
  const getCustomsTooltip = (taxValues) => {
    if (!taxValues || taxValues.length === 0) return ''
    return taxValues
      .map(tv => `Country ${tv.country}: ${tv.tax_value || 'N/A'}`)
      .join('\n')
  }

  // Row component for List (table layout)
  const Row = ({ index, style, items, onCopyCode }) => {
    const item = items[index]
    if (!item) return null

    const displayName = item.name_ro || item.name_ru || item.name_en || 'Unnamed'
    const displayCode = item.nc
    const customsRate = getPrimaryCustomsRate(item.tax_values)
    const customsTooltip = getCustomsTooltip(item.tax_values)

    return (
      <div style={style} className="table-row">
        <div className="table-cell table-cell-code"
             onClick={() => onCopyCode(displayCode)}
             title={displayCode ? 'Click to copy' : ''}
             style={{ cursor: displayCode ? 'pointer' : 'default' }}>
          {displayCode || '\u00A0'}
        </div>
        <div className="table-cell table-cell-name"
             style={{ paddingLeft: `${item.level * 24}px` }}
             title={displayName}>
          {displayName}
        </div>
        <div className="table-cell table-cell-tax">
          {item.vat || '-'}
        </div>
        <div className="table-cell table-cell-tax table-cell-tax-customs"
             title={customsTooltip}>
          {customsRate}
        </div>
        <div className="table-cell table-cell-tax">
          {item.excise || '-'}
        </div>
      </div>
    )
  }

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
        <div className="table-header">
          <div className="table-cell table-cell-code">NC Code</div>
          <div className="table-cell table-cell-name">Name</div>
          <div className="table-cell table-cell-tax">
            VAT <span className="info-icon" title="Value Added Tax - Domestic consumption tax">ⓘ</span>
          </div>
          <div className="table-cell table-cell-tax table-cell-tax-customs">
            Customs <span className="info-icon" title="Import duty rates by country (hover row for details)">ⓘ</span>
          </div>
          <div className="table-cell table-cell-tax">
            Excise <span className="info-icon" title="Excise tax for specific goods (alcohol, tobacco, fuel, etc.)">ⓘ</span>
          </div>
        </div>
        {filteredData.length > 0 ? (
          <List
            rowComponent={Row}
            rowCount={filteredData.length}
            rowHeight={32}
            rowProps={{ items: filteredData, onCopyCode: copyToClipboard }}
          />
        ) : (
          <div className="no-items">No items found</div>
        )}
      </div>
    </div>
  )
}

export default Home
