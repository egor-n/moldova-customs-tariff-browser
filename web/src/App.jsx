import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import './App.css'
import Home from './pages/Home'
import Category from './pages/Category'

function App() {
  return (
    <Router>
      <div className="app">
        <header className="header">
          <div className="container">
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
          <div className="container">
            <p>Data sourced from trade.gov.md</p>
          </div>
        </footer>
      </div>
    </Router>
  )
}

export default App
