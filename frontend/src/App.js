import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import Home from './components/Home';
import DigestSimulator from './components/DigestSimulator';
import PreferencePage from './components/preferences/PreferencePage';
import EmailVerificationPage from './pages/EmailVerificationPage';
import './App.css';
import './styles/responsive.css';

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
            Home
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
            <Route path="/" element={<Home />} />
            <Route path="/digest-simulator" element={<DigestSimulator />} />
            <Route path="/preferences/:token" element={<PreferencePage />} />
            <Route path="/verify-email" element={<EmailVerificationPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
