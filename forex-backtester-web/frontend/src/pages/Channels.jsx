import { useState, useEffect } from 'react'
import { api } from '../utils/api'
import { useSession } from '../hooks/useSession'
import { Card, Input, Select, Button, SectionTitle, Badge } from '../components/UI'
import { Plus, Trash2, Hash } from 'lucide-react'

export default function Channels() {
  const { session } = useSession()
  const [channels, setChannels] = useState([])
  const [form, setForm]         = useState({ name: '', channel_id: '', parser: 'generic' })
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState(null)

  useEffect(() => { loadChannels() }, [session])

  async function loadChannels() {
    const data = await api.getChannels(session).catch(() => [])
    setChannels(data)
  }

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  async function handleAdd() {
    if (!form.name || !form.channel_id) return
    setLoading(true); setError(null)
    try {
      await api.addChannel({ ...form, session_name: session })
      setForm({ name: '', channel_id: '', parser: 'generic' })
      loadChannels()
    } catch (e) { setError(e.message) }
    finally { setLoading(false) }
  }

  async function handleDelete(id) {
    await api.deleteChannel(id, session)
    loadChannels()
  }

  return (
    <div className="p-8 max-w-2xl animate-fade-in">
      <SectionTitle>Signal Sources</SectionTitle>
      <h1 className="text-2xl font-display text-text mb-1">Channels</h1>
      <p className="text-muted text-sm mb-8">Add the Telegram channels or groups your signal providers use.</p>

      {/* Add form */}
      <Card className="mb-6">
        <p className="text-xs font-display text-muted uppercase tracking-widest mb-4">Add Channel</p>
        <div className="grid grid-cols-2 gap-4 mb-4">
          <Input label="Channel Name" value={form.name}
            onChange={e => set('name', e.target.value)} placeholder="Provider A" />
          <Input label="Channel ID" value={form.channel_id}
            onChange={e => set('channel_id', e.target.value)} placeholder="-1001234567890" />
        </div>
        <div className="flex items-end gap-4">
          <div className="flex-1">
            <Select label="Parser" value={form.parser} onChange={e => set('parser', e.target.value)}>
              <option value="generic">Generic (auto-detect)</option>
            </Select>
          </div>
          <Button onClick={handleAdd} loading={loading}>
            <Plus size={14} /> Add Channel
          </Button>
        </div>
        {error && <p className="text-red text-xs mt-3">{error}</p>}
      </Card>

      {/* How to get channel ID */}
      <div className="mb-6 p-4 bg-surface border border-border rounded-xl">
        <p className="text-xs font-display text-muted uppercase tracking-widest mb-2">How to get Channel ID</p>
        <p className="text-sm text-muted">
          Forward any message from the channel to <span className="text-accent">@userinfobot</span> on Telegram.
          The bot will reply with the channel ID (starts with <span className="text-text font-display">-100</span>).
        </p>
      </div>

      {/* Channels list */}
      {channels.length === 0 ? (
        <div className="text-center py-12 text-muted">
          <Hash size={32} className="mx-auto mb-3 opacity-30" />
          <p className="text-sm">No channels added yet.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {channels.map(ch => (
            <div key={ch.id} className="flex items-center justify-between bg-card border border-border rounded-xl px-5 py-4">
              <div>
                <p className="text-text font-medium text-sm">{ch.name}</p>
                <p className="text-muted text-xs font-display mt-0.5">ID: {ch.channel_id}</p>
              </div>
              <div className="flex items-center gap-3">
                <Badge variant="default">{ch.parser}</Badge>
                <button onClick={() => handleDelete(ch.id)} className="text-muted hover:text-red transition-colors">
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
