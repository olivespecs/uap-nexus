import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'

interface Incident {
  id: string
  source: string
  agency: string
  location_name: string
  incident_date: string
  craft_description: string
  resolution: string
  tags: string[]
}

export default function TimelineWidget() {
  const [events, setEvents] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/crawler/history?hours=168')
      .then(r => r.json())
      .then(data => {
        setEvents(data.releases || [])
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  if (loading) {
    return <div>Loading timeline...</div>
  }

  return (
    <div>
      <h2 style={{ marginBottom: '1rem' }}>PURSUE Timeline</h2>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        {events.length === 0 ? (
          <p style={{ color: 'var(--text-secondary)' }}>No releases detected yet. Run crawler to capture.</p>
        ) : (
          events.slice(0, 20).map((event, i) => (
            <div key={i} className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                  {new Date(event.timestamp).toLocaleDateString()}
                </span>
                <p style={{ fontWeight: 500 }}>
                  {event.count} {event.sources?.join(', ')} releases
                </p>
              </div>
              <span className="badge badge-new">NEW</span>
            </div>
          ))
        )}
      </div>
    </div>
  )
}