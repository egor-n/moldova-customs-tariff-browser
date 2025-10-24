import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import './App.css'
import Home from './pages/Home'
import Category from './pages/Category'

function App() {
  return (
    <Router>
      <div className="app">
        <header className="header">
          <div className="header-content">
            <Link to="/" className="logo">
              <h1>Moldova Tariff Nomenclature</h1>
            </Link>
          </div>
        </header>

        <main className="main">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/category/:id" element={<Category />} />
          </Routes>
        </main>

        <footer className="footer">
          <div className="footer-content">
            <a href="https://ecustoms.trade.gov.md/declaration-post" target="_blank" rel="noopener noreferrer">
              Declare postal packages
            </a>
            <span>Data sourced from trade.gov.md</span>
          </div>
        </footer>
      </div>
    </Router>
  )
}

export default App
