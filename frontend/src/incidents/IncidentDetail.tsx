import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'

export default function IncidentDetail() {
  const { id } = useParams()
  const [incident, setIncident] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`/api/incidents/${id}`)
      .then(r => r.json())
      .then(data => {
        setIncident(data)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [id])

  if (loading) {
    return <div>Loading incident...</div>
  }

  if (!incident) {
    return <div>Incident not found</div>
  }

  return (
    <div>
      <Link to="/incidents" style={{ marginBottom: '1rem', display: 'block' }}>← Back to incidents</Link>
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '1rem' }}>
          <div>
            <span className="badge" style={{ background: 'var(--bg-tertiary)', marginRight: '0.5rem' }}>{incident.source}</span>
            <span className={`badge ${incident.resolution === 'RESOLVED' ? '' : 'badge-new'}`}>{incident.resolution}</span>
          </div>
          {incident.raw_doc_url && (
            <a href={incident.raw_doc_url} target="_blank" rel="noopener" className="btn btn-primary">
              View Document
            </a>
          )}
        </div>
        <h2>{incident.location_name || 'Unknown Location'}</h2>
        {incident.incident_date && <p style={{ color: 'var(--text-secondary)' }}>Date: {incident.incident_date}</p>}
        {incident.agency && <p style={{ color: 'var(--text-secondary)' }}>Agency: {incident.agency}</p>}
        <hr style={{ border: 'none', borderTop: '1px solid var(--bg-tertiary)', margin: '1rem 0' }} />
        <h3>Craft Description</h3>
        <p style={{ marginBottom: '1rem' }}>{incident.craft_description || 'No description available'}</p>
        {incident.extracted_text && (
          <>
            <h3>Extracted Text</h3>
            <pre style={{ background: 'var(--bg-tertiary)', padding: '1rem', borderRadius: '6px', overflow: 'auto', maxHeight: '300px', whiteSpace: 'pre-wrap', fontSize: '0.875rem' }}>
              {incident.extracted_text.slice(0, 2000)}...
            </pre>
          </>
        )}
        {incident.tags?.length > 0 && (
          <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            {incident.tags.map((tag: string) => (
              <span key={tag} className="badge" style={{ background: 'var(--bg-tertiary)' }}>{tag}</span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}