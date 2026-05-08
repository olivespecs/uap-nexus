import { useState, useEffect } from 'react'

export default function AlertsPage() {
  const [channels, setChannels] = useState<any>({})
  const [subscriptions, setSubscriptions] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      fetch('/api/alerts/channels').then(r => r.json()),
      fetch('/api/alerts/subscriptions').then(r => r.json()),
    ]).then(([ch, sub]) => {
      setChannels(ch.channels || {})
      setSubscriptions(sub.subscriptions || [])
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  if (loading) {
    return <div>Loading alerts...</div>
  }

  return (
    <div>
      <h2 style={{ marginBottom: '1rem' }}>Alert Configuration</h2>
      <div className="card" style={{ marginBottom: '1rem' }}>
        <h3>Available Channels</h3>
        <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem' }}>
          <div className={channels.telegram ? 'badge-new' : 'badge'} style={{ background: channels.telegram ? 'var(--accent)' : 'var(--bg-tertiary)', color: channels.telegram ? 'var(--bg-primary)' : 'var(--text-secondary)' }}>
            Telegram {channels.telegram ? '✓' : '✗'}
          </div>
          <div className={channels.discord ? 'badge-new' : 'badge'} style={{ background: channels.discord ? 'var(--accent)' : 'var(--bg-tertiary)', color: channels.discord ? 'var(--bg-primary)' : 'var(--text-secondary)' }}>
            Discord {channels.discord ? '✓' : '✗'}
          </div>
          <div className={channels.email ? 'badge-new' : 'badge'} style={{ background: channels.email ? 'var(--accent)' : 'var(--bg-tertiary)', color: channels.email ? 'var(--bg-primary)' : 'var(--text-secondary)' }}>
            Email {channels.email ? '✓' : '✗'}
          </div>
        </div>
      </div>
      <div className="card">
        <h3>Active Subscriptions ({subscriptions.length})</h3>
        {subscriptions.length === 0 ? (
          <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>No subscriptions yet</p>
        ) : (
          <ul style={{ marginTop: '0.5rem', paddingLeft: '1rem' }}>
            {subscriptions.map((sub: any) => (
              <li key={sub.id} style={{ marginBottom: '0.25rem' }}>
                {sub.channel_type}: {sub.channel_id} ({sub.filters?.source || 'all sources'})
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}