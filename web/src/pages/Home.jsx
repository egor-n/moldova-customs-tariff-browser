import { useState, useEffect, useMemo } from 'react'
import { Link } from 'react-router-dom'

function TreeNode({ node, level = 0, filter }) {
  const [isOpen, setIsOpen] = useState(level < 2) // Auto-expand first 2 levels
  const hasChildren = node.children && node.children.length > 0

  const displayName = node.name_ro || node.name_ru || node.name_en || 'Unnamed'
  const displayCode = node.nc || ''

  // Auto-expand if filter is active and has matching children
  useEffect(() => {
    if (filter && hasChildren) {
      setIsOpen(true)
    }
  }, [filter, hasChildren])

  // Check if this node or any child matches filter
  const matchesFilter = useMemo(() => {
    if (!filter || !filter.trim()) return true

    const searchLower = filter.toLowerCase().trim()
    const nodeMatches =
      displayName.toLowerCase().includes(searchLower) ||
      displayCode.toLowerCase().includes(searchLower)

    // If this node matches, show it
    if (nodeMatches) return true

    // Check if any child matches (recursive)
    const hasMatchingChild = (currentNode) => {
      if (!currentNode.children || currentNode.children.length === 0) return false

      return currentNode.children.some(child => {
        const childName = (child.name_ro || child.name_ru || child.name_en || '').toLowerCase()
        const childCode = (child.nc || '').toLowerCase()

        // Check if this child matches
        if (childName.includes(searchLower) || childCode.includes(searchLower)) {
          return true
        }

        // Recursively check child's children
        return hasMatchingChild(child)
      })
    }

    return hasMatchingChild(node)
  }, [filter, displayName, displayCode, node])

  if (!matchesFilter) return null

  return (
    <div className="tree-node">
      <div
        className="tree-node-content"
        style={{ paddingLeft: `${level * 24}px` }}
      >
        {hasChildren && (
          <button
            className="tree-toggle"
            onClick={() => setIsOpen(!isOpen)}
            aria-label={isOpen ? 'Collapse' : 'Expand'}
          >
            {isOpen ? '▼' : '▶'}
          </button>
        )}
        {!hasChildren && <span className="tree-spacer"></span>}

        <Link
          to={`/category/${node.id}`}
          className="tree-node-link"
        >
          {displayCode && <span className="tree-code">{displayCode}</span>}
          <span className="tree-name">{displayName}</span>
          {node.import_acts && node.import_acts.length > 0 && (
            <span className="tree-badge">{node.import_acts.length} acts</span>
          )}
        </Link>
      </div>

      {hasChildren && isOpen && (
        <div className="tree-children">
          {node.children.map(child => (
            <TreeNode
              key={child.id}
              node={child}
              level={level + 1}
              filter={filter}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function Home() {
  const [treeData, setTreeData] = useState([])
  const [filter, setFilter] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/data/nomenclature_tree.json')
      .then(res => res.json())
      .then(data => {
        setTreeData(data)
        setLoading(false)
      })
      .catch(err => {
        console.error('Error loading data:', err)
        setLoading(false)
      })
  }, [])

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
      </div>

      <div className="tree-view">
        {treeData.map(node => (
          <TreeNode
            key={node.id}
            node={node}
            filter={filter}
          />
        ))}
      </div>
    </div>
  )
}

export default Home
