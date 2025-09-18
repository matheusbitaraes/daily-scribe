import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import NewsPage from './pages/NewsPage';
import DigestSimulator from './components/DigestSimulator';
import PreferencePage from './components/preferences/PreferencePage';
import EmailVerificationPage from './pages/EmailVerificationPage';
import UnsubscribePage from './pages/UnsubscribePage';
import { createTheme, ThemeProvider } from '@mui/material/styles';

const theme = createTheme({
  typography: {
    fontFamily: [
      'Georgia', 'Times New Roman', 'Times', 'serif', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Oxygen',
    ].join(','),
  },
      
})
function App() {
  return (
    <ThemeProvider theme={theme}>
      <link href="https://fonts.googleapis.com/icon?family=Material+Icons"
      rel="stylesheet"></link>
      <Router>
        <div className="App">
          {/* <Navigation /> */}
          <main className="app-main">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/news" element={<NewsPage />} />
              <Route path="/digest-simulator" element={<DigestSimulator />} />
              <Route path="/preferences/:token" element={<PreferencePage />} />
              <Route path="/verify-email" element={<EmailVerificationPage />} />
              <Route path="/unsubscribe/:token" element={<UnsubscribePage />} />
            </Routes>
          </main>
        </div>
      </Router>
    </ThemeProvider>
  );
}

export default App;
