import { useState, useEffect } from 'react'

interface Incident {
  id: string
  source: string
  agency: string
  location_name: string
  incident_date: string
  craft_description: string
  resolution: string
  tags: string[]
  is_new: boolean
}

export default function IncidentList() {
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('')

  useEffect(() => {
    fetch('/api/incidents?limit=100')
      .then(r => r.json())
      .then(data => {
        setIncidents(data.incidents || [])
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  const filtered = incidents.filter(inc =>
    filter === '' ||
    inc.source === filter ||
    inc.agency?.toLowerCase().includes(filter.toLowerCase())
  )

  if (loading) {
    return <div>Loading incidents...</div>
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h2>Incidents ({filtered.length})</h2>
        <input
          type="text"
          placeholder="Search..."
          value={filter}
          onChange={e => setFilter(e.target.value)}
          className="btn btn-secondary"
          style={{ width: '200px' }}
        />
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        {filtered.length === 0 ? (
          <p style={{ color: 'var(--text-secondary)' }}>No incidents yet. Run crawler to capture releases.</p>
        ) : (
          filtered.map(inc => (
            <Link key={inc.id} to={`/incidents/${inc.id}`} className="card" style={{ display: 'block', textDecoration: 'none' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                <div>
                  <span className="badge" style={{ background: 'var(--bg-tertiary)', marginRight: '0.5rem' }}>
                    {inc.source}
                  </span>
                  {inc.is_new && <span className="badge badge-new">NEW</span>}
                  <h3 style={{ marginTop: '0.5rem', fontSize: '1rem' }}>{inc.location_name || 'Unknown Location'}</h3>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>{inc.craft_description?.slice(0, 100)}</p>
                </div>
                <div style={{ textAlign: 'right', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                  {inc.incident_date && <p>{inc.incident_date}</p>}
                  {inc.agency && <p>{inc.agency}</p>}
                </div>
              </div>
            </Link>
          ))
        )}
      </div>
    </div>
  )
}