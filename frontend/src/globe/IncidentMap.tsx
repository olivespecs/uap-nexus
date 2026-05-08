import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'

interface Incident {
  id: string
  source: string
  agency: string
  location_name: string
  lat: number
  lon: number
  incident_date: string
  craft_description: string
  tags: string[]
}

export default function IncidentMap() {
  const mapContainer = useRef<HTMLDivElement>(null)
  const map = useRef<mapboxgl.Map | null>(null)
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [hovered, setHovered] = useState<Incident | null>(null)
  const navigate = useNavigate()

  useEffect(() => {
    fetch('/api/incidents?limit=100')
      .then(r => r.json())
      .then(data => {
        const incidents = data.incidents || []
        setIncidents(incidents)
        addMarkers(incidents)
      })
      .catch(console.error)
  }, [])

  function addMarkers(incidents: Incident[]) {
    if (!map.current) return

    // This would add actual mapbox markers in real implementation
    // For now, incidents list is displayed
  }

  return (
    <div>
      <div ref={mapContainer} style={{ height: '600px', background: 'var(--bg-secondary)', borderRadius: '8px', overflow: 'hidden' }}>
        <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ fontSize: '4rem' }}>🌍</div>
          <p style={{ color: 'var(--text-secondary)' }}>3D Globe with {incidents.length} incidents</p>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>Mapbox integration → add MAPBOX_TOKEN to .env</p>
          <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap', maxWidth: '600px', justifyContent: 'center' }}>
            {incidents.slice(0, 10).map(inc => (
              <button
                key={inc.id}
                className="badge badge-new"
                onClick={() => navigate(`/incidents/${inc.id}`)}
              >
                {inc.location_name || inc.id.slice(0, 8)}
              </button>
            ))}
          </div>
        </div>
      </div>
      <div style={{ marginTop: '1rem', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
        <select className="btn btn-secondary">
          <option>All Sources</option>
          <option>PURSUE</option>
          <option>AARO</option>
          <option>FOIA</option>
        </select>
        <select className="btn btn-secondary">
          <option>All Eras</option>
          <option>2000s</option>
          <option>2010s</option>
          <option>2020s</option>
        </select>
        <select className="btn btn-secondary">
          <option>All Agencies</option>
          <option>USAF</option>
          <option>Navy</option>
          <option>DARPA</option>
        </select>
      </div>
    </div>
  )
}

declare var mapboxgl: any