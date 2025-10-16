import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'

function Category() {
  const { id } = useParams()
  const [category, setCategory] = useState(null)
  const [children, setChildren] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/data/nomenclature_flat.json')
      .then(res => res.json())
      .then(data => {
        // Find the category
        const item = data.find(item => item.id === parseInt(id))
        setCategory(item)

        // Find children
        if (item && item.children && item.children.length > 0) {
          const childItems = data.filter(d => item.children.includes(d.id))
          setChildren(childItems)
        }

        setLoading(false)
      })
      .catch(err => {
        console.error('Error loading data:', err)
        setLoading(false)
      })
  }, [id])

  if (loading) {
    return (
      <div className="container">
        <div className="loading">Loading...</div>
      </div>
    )
  }

  if (!category) {
    return (
      <div className="container">
        <div className="error">Category not found</div>
      </div>
    )
  }

  return (
    <div className="container">
      <div className="category-page">
        <div className="breadcrumbs">
          <Link to="/">Home</Link>
          {category.path && (
            <>
              <span className="separator">/</span>
              <span>{category.path}</span>
            </>
          )}
        </div>

        <div className="category-header">
          <div className="category-code">
            <span className="nc-code-large">{category.nc_code}</span>
            {category.is_leaf && <span className="badge badge-leaf">Leaf Category</span>}
          </div>
          <h2 className="category-title">{category.name_ro || category.name_ru || category.name_en}</h2>
        </div>

        <div className="category-details">
          {category.name_ro && (
            <div className="detail-row">
              <span className="detail-label">Romanian:</span>
              <span className="detail-value">{category.name_ro}</span>
            </div>
          )}
          {category.name_ru && (
            <div className="detail-row">
              <span className="detail-label">Russian:</span>
              <span className="detail-value">{category.name_ru}</span>
            </div>
          )}
          {category.name_en && (
            <div className="detail-row">
              <span className="detail-label">English:</span>
              <span className="detail-value">{category.name_en}</span>
            </div>
          )}
          <div className="detail-row">
            <span className="detail-label">Level:</span>
            <span className="detail-value">{category.level}</span>
          </div>
          {category.parent_id && (
            <div className="detail-row">
              <span className="detail-label">Parent ID:</span>
              <span className="detail-value">{category.parent_id}</span>
            </div>
          )}
        </div>

        {category.import_acts && category.import_acts.length > 0 && (
          <div className="section">
            <h3>Regulatory Acts ({category.import_acts.length})</h3>
            <div className="acts-list">
              {category.import_acts.map((act, idx) => (
                <div key={idx} className="act-card">
                  <div className="act-number">{act.act_number || 'N/A'}</div>
                  <div className="act-details">
                    {act.article && <div><strong>Article:</strong> {act.article}</div>}
                    {act.annex && <div><strong>Annex:</strong> {act.annex}</div>}
                    {act.type && <div><strong>Type:</strong> {act.type}</div>}
                    {act.point && <div><strong>Point:</strong> {act.point}</div>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {children.length > 0 && (
          <div className="section">
            <h3>Subcategories ({children.length})</h3>
            <div className="children-list">
              {children.map(child => (
                <Link
                  key={child.id}
                  to={`/category/${child.id}`}
                  className="child-card"
                >
                  <div className="child-code">{child.nc_code}</div>
                  <div className="child-name">{child.name_ro || child.name_ru || child.name_en}</div>
                  {child.is_leaf && <span className="badge">Leaf</span>}
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default Category
