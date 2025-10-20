import { useState, useEffect, useMemo } from 'react'
import { List } from 'react-window'
import Fuse from 'fuse.js'
import { COUNTRIES, DEFAULT_COUNTRY_ID } from '../config/countries'

function Home() {
  const [flatData, setFlatData] = useState([])
  const [filter, setFilter] = useState('')
  const [debouncedFilter, setDebouncedFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [toast, setToast] = useState({ show: false, message: '' })
  const [selectedCountry, setSelectedCountry] = useState(DEFAULT_COUNTRY_ID)

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

  const generateMarkdown = (data) => {
    let markdown = '# Moldova Customs Tariff Nomenclature\n\n'
    markdown += `Generated: ${new Date().toISOString().split('T')[0]}\n`
    markdown += `Total Items: ${data.length.toLocaleString()}\n`
    markdown += `Source: https://trade.gov.md\n\n---\n\n`

    data.forEach(item => {
      const indent = '  '.repeat(item.level)
      const displayName = item.name_ro || item.name_ru || item.name_en || 'Unnamed'

      if (item.nc) {
        markdown += `${indent}- **${item.nc}** - ${displayName}\n`
      } else {
        markdown += `${indent}- ${displayName}\n`
      }
    })

    return markdown
  }

  const handleDownload = () => {
    const markdown = generateMarkdown(flatData)
    const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `moldova-tariff-nomenclature-${new Date().toISOString().split('T')[0]}.md`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)

    setToast({ show: true, message: 'Download started!' })
    setTimeout(() => setToast({ show: false, message: '' }), 2000)
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
        // Flatten the tree into a simple array with level info and parent tracking
        const flattened = []
        const idToIndex = new Map() // Map item ID to its index in flattened array

        const flatten = (nodes, level = 0, parentIds = []) => {
          nodes.forEach(node => {
            const taxInfo = node.tax_info || {}
            const currentIndex = flattened.length

            idToIndex.set(node.id, currentIndex)

            flattened.push({
              id: node.id,
              nc: node.nc || '',
              name_ro: node.name_ro || '',
              name_ru: node.name_ru || '',
              name_en: node.name_en || '',
              import_acts: node.import_acts || [],
              level,
              parentIds: [...parentIds], // Store chain of parent IDs
              indexInTree: currentIndex, // Store original tree order
              // Tax information
              vat: taxInfo.vat || '',
              excise: taxInfo.excise || '',
              tax_values: taxInfo.tax_values || []
            })
            if (node.children && node.children.length > 0) {
              flatten(node.children, level + 1, [...parentIds, node.id])
            }
          })
        }
        flatten(data)

        // Store the ID-to-index map for later use
        flattened.forEach(item => {
          item._idToIndex = idToIndex
        })

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
      threshold: 0.1,        // 0 = exact, 1 = match anything (0.1 = low fuzziness, stricter matching)
      distance: 100,         // Max distance from start for typo
      ignoreLocation: true,  // Match anywhere in string
      minMatchCharLength: 2  // Minimum characters to trigger match
    })
  }, [flatData])

  // Helper to include parent items for context
  const includeParents = (matchedItems) => {
    if (!matchedItems || !matchedItems.length) return []

    const itemsToShow = new Set()

    // For each matched item, include it and all its parents
    matchedItems.forEach(item => {
      if (!item) return

      itemsToShow.add(item.id)

      // Add all parent IDs if they exist
      if (item.parentIds && Array.isArray(item.parentIds)) {
        item.parentIds.forEach(parentId => {
          itemsToShow.add(parentId)
        })
      }
    })

    // Get all items (matched + parents) and sort by original tree order
    return flatData
      .filter(item => itemsToShow.has(item.id))
      .sort((a, b) => a.indexInTree - b.indexInTree)
  }

  // Filter the flat list with fuzzy search
  const filteredData = useMemo(() => {
    if (!debouncedFilter.trim()) return flatData

    const searchTrimmed = debouncedFilter.trim()
    let matchedItems = []

    // Exact search - wrapped in double quotes
    const isExactSearch = searchTrimmed.startsWith('"') && searchTrimmed.endsWith('"')
    if (isExactSearch) {
      const exactValue = searchTrimmed.slice(1, -1) // Remove quotes
      const exactNormalized = normalizeText(exactValue)

      matchedItems = flatData.filter(item => {
        const nameRo = normalizeText(item.name_ro)
        const nameRu = normalizeText(item.name_ru)
        const nameEn = normalizeText(item.name_en)
        const nc = normalizeText(item.nc)

        return nameRo.includes(exactNormalized) ||
               nameRu.includes(exactNormalized) ||
               nameEn.includes(exactNormalized) ||
               nc.includes(exactNormalized)
      })
      return includeParents(matchedItems)
    }

    const isWildcard = searchTrimmed.endsWith('*')
    const searchValue = isWildcard ? searchTrimmed.slice(0, -1) : searchTrimmed

    // Wildcard search - exact prefix match on NC codes
    if (isWildcard) {
      const searchNormalized = normalizeText(searchValue).replace(/\s/g, '')
      matchedItems = flatData.filter(item => {
        const displayCode = normalizeText(item.nc)
        return displayCode.startsWith(searchNormalized)
      })
      return includeParents(matchedItems)
    }

    // Check if search is numeric (NC code search) - allow spaces in between
    const searchValueNoSpaces = searchValue.replace(/\s/g, '')
    const isNumericSearch = /^[0-9]+$/.test(searchValueNoSpaces)

    if (isNumericSearch) {
      // Exact match for NC codes (no fuzzy) - remove spaces from input
      matchedItems = flatData.filter(item => item.nc.includes(searchValueNoSpaces))
      return includeParents(matchedItems)
    }

    // Fuzzy search for text queries
    const results = fuse.search(searchValue)
    matchedItems = results.map(result => result.item)
    return includeParents(matchedItems)
  }, [flatData, debouncedFilter, fuse])

  // Helper to get customs rate for selected country
  const getCustomsRate = (taxValues, countryId) => {
    if (!taxValues || taxValues.length === 0) return '-'
    const countryRate = taxValues.find(tv => tv.country === countryId)
    if (countryRate && countryRate.tax_value && countryRate.tax_value.trim()) {
      return countryRate.tax_value
    }
    return '-'
  }

  // Helper to format customs tooltip
  const getCustomsTooltip = (taxValues) => {
    if (!taxValues || taxValues.length === 0) return ''
    return taxValues
      .filter(tv => tv.tax_value && tv.tax_value.trim())
      .map(tv => `${COUNTRIES[tv.country] || `Country ${tv.country}`}: ${tv.tax_value}`)
      .join('\n')
  }

  // Row component for List (table layout)
  const Row = ({ index, style, items, onCopyCode, countryId }) => {
    const item = items[index]
    if (!item) return null

    const displayName = item.name_ro || item.name_ru || item.name_en || 'Unnamed'
    const displayCode = item.nc
    const customsRate = getCustomsRate(item.tax_values, countryId)
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

      <div className="download-section">
        <div className="download-info">
          <h3>LLM-Ready Export</h3>
          <p>Export all {flatData.length.toLocaleString()} items as markdown (~{(flatData.length * 75 / 1024 / 1024).toFixed(1)} MB).</p>
          <div className="download-sample">
            <span className="download-sample-icon">i</span>
            <span>View sample</span>
            <div className="download-sample-tooltip">
              {`- **0101** - Cai, măgari, catâri şi bardoi, vii:
  - **010121000** - – – Cai
  - **010129000** - – – Altele
- **0102** - Animale vii din specia bovine
  - **01022100** - – – Din rase pentru reproducţie
    - **010221001** - – – – Vaci

...`}
            </div>
          </div>
        </div>
        <button className="download-button" onClick={handleDownload}>
          <span className="download-icon">↓</span>
          Download
        </button>
      </div>

      <div className="tree-header">
        <input
          type="text"
          placeholder='Search... (use "quotes" for exact match, * for wildcard)'
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
        <select
          value={selectedCountry}
          onChange={(e) => setSelectedCountry(Number(e.target.value))}
          className="country-filter"
          title="Select country for customs rates"
        >
          {Object.entries(COUNTRIES).map(([id, name]) => (
            <option key={id} value={id}>
              {name}
            </option>
          ))}
        </select>
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
        <div style={{ flex: 1, minHeight: 0 }}>
          {filteredData.length > 0 ? (
            <List
              rowComponent={Row}
              rowCount={filteredData.length}
              rowHeight={32}
              rowProps={{ items: filteredData, onCopyCode: copyToClipboard, countryId: selectedCountry }}
            />
          ) : (
            <div className="no-items">No items found</div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Home
