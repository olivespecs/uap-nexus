import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import IncidentMap from './globe/IncidentMap'
import TimelineWidget from './timeline/TimelineWidget'
import IncidentList from './incidents/IncidentList'
import IncidentDetail from './incidents/IncidentDetail'
import AlertsPage from './alerts/AlertsPage'
import './globe/mapbox.css'

const queryClient = new QueryClient()

function Nav() {
  const location = useLocation()

  return (
    <nav className="nav">
      <Link to="/" className={location.pathname === '/' ? 'active' : ''}>Map</Link>
      <Link to="/incidents" className={location.pathname.startsWith('/incidents') ? 'active' : ''}>Incidents</Link>
      <Link to="/timeline" className={location.pathname === '/timeline' ? 'active' : ''}>Timeline</Link>
      <Link to="/alerts" className={location.pathname === '/alerts' ? 'active' : ''}>Alerts</Link>
    </nav>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="container">
          <header style={{ padding: '1rem 0', borderBottom: '1px solid var(--bg-tertiary)', marginBottom: '1rem' }}>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>
              <span style={{ color: 'var(--accent)' }}>UAP</span> NEXUS
            </h1>
          </header>
          <Nav />
          <Routes>
            <Route path="/" element={<IncidentMap />} />
            <Route path="/incidents" element={<IncidentList />} />
            <Route path="/incidents/:id" element={<IncidentDetail />} />
            <Route path="/timeline" element={<TimelineWidget />} />
            <Route path="/alerts" element={<AlertsPage />} />
          </Routes>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App