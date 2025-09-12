import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import DigestSimulator from './components/DigestSimulator';
import PreferencePage from './components/preferences/PreferencePage';
import EmailVerificationPage from './pages/EmailVerificationPage';
import UnsubscribePage from './pages/UnsubscribePage';
import './App.css';
import './styles/responsive.css';


function App() {
  return (
    <Router>
      <div className="App">
        {/* <Navigation /> */}
        <main className="app-main">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/digest-simulator" element={<DigestSimulator />} />
            <Route path="/preferences/:token" element={<PreferencePage />} />
            <Route path="/verify-email" element={<EmailVerificationPage />} />
            <Route path="/unsubscribe/:token" element={<UnsubscribePage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
