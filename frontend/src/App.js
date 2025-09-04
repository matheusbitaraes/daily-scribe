import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import ArticleList from './ArticleList';
import DigestSimulator from './components/DigestSimulator';
import './App.css';

// Navigation component
function Navigation() {
  const location = useLocation();
  
  return (
    <nav className="app-navigation">
      <div className="nav-container">
        <div className="nav-brand">
          <Link to="/" className="brand-link">Daily Scribe</Link>
        </div>
        <div className="nav-links">
          <Link 
            to="/" 
            className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}
          >
            Articles
          </Link>
          <Link 
            to="/digest-simulator" 
            className={`nav-link ${location.pathname === '/digest-simulator' ? 'active' : ''}`}
          >
            Digest Simulator
          </Link>
        </div>
      </div>
    </nav>
  );
}

function App() {
  return (
    <Router>
      <div className="App">
        <Navigation />
        <main className="app-main">
          <Routes>
            <Route path="/" element={<ArticleList />} />
            <Route path="/digest-simulator" element={<DigestSimulator />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
