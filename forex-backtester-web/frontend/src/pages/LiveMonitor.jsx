import { useState, useEffect, useRef } from 'react'
import { useSession } from '../hooks/useSession'
import { Badge, Button, SectionTitle, Dot } from '../components/UI'
import { Radio, StopCircle } from 'lucide-react'

export default function LiveMonitor() {
  const { session } = useSession()
  const [signals, setSignals] = useState([])
  const [active, setActive]   = useState(false)
  const [status, setStatus]   = useState('idle') // idle | connecting | live | error
  const wsRef                 = useRef(null)
  const feedRef               = useRef(null)

  function connect() {
    setStatus('connecting')
    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const ws    = new WebSocket(`${proto}://${window.location.host}/ws/live?session_name=${session}`)
    wsRef.current = ws

    ws.onopen    = () => { setActive(true); setStatus('live') }
    ws.onclose   = () => { setActive(false); setStatus('idle') }
    ws.onerror   = () => { setActive(false); setStatus('error') }
    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data)
      if (msg.type === 'signal') {
        setSignals(s => [msg.data, ...s].slice(0, 100))
        setTimeout(() => feedRef.current?.scrollTo(0, 0), 50)
      }
    }
  }

  function disconnect() {
    wsRef.current?.close()
    setActive(false); setStatus('idle')
  }

  useEffect(() => () => wsRef.current?.close(), [])

  const statusColor = { idle: 'text-muted', connecting: 'text-gold', live: 'text-accent', error: 'text-red' }

  return (
    <div className="p-8 animate-fade-in">
      <SectionTitle>Real-Time</SectionTitle>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-display text-text mb-1">Live Monitor</h1>
          <p className="text-muted text-sm">Signals appear here as they arrive in your channels.</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Dot active={active} />
            <span className={`text-xs font-display uppercase ${statusColor[status]}`}>{status}</span>
          </div>
          {active
            ? <Button variant="danger" onClick={disconnect}><StopCircle size={14} /> Stop</Button>
            : <Button onClick={connect} loading={status === 'connecting'}>
                <Radio size={14} /> Start Listening
              </Button>
          }
        </div>
      </div>

      {signals.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64 text-muted">
          <Radio size={40} className="mb-4 opacity-20" />
          <p className="text-sm">{active ? 'Waiting for signals...' : 'Click "Start Listening" to monitor channels.'}</p>
        </div>
      ) : (
        <div ref={feedRef} className="space-y-2 max-h-[calc(100vh-220px)] overflow-y-auto">
          {signals.map((sig, i) => (
            <div key={i} className="flex items-center gap-4 bg-card border border-border rounded-xl px-5 py-4 animate-fade-in">
              <div className="w-2 h-2 rounded-full bg-accent pulse-dot" />
              <div className="flex-1 grid grid-cols-6 gap-4 text-sm">
                <div>
                  <p className="text-muted text-xs font-display">PAIR</p>
                  <p className="text-text font-display font-medium">{sig.pair || '—'}</p>
                </div>
                <div>
                  <p className="text-muted text-xs font-display">DIRECTION</p>
                  <Badge variant={sig.direction === 'BUY' ? 'win' : 'loss'}>{sig.direction}</Badge>
                </div>
                <div>
                  <p className="text-muted text-xs font-display">ENTRY</p>
                  <p className="text-text font-display">{sig.entry}</p>
                </div>
                <div>
                  <p className="text-muted text-xs font-display">SL</p>
                  <p className="text-red font-display">{sig.sl}</p>
                </div>
                <div>
                  <p className="text-muted text-xs font-display">TP1</p>
                  <p className="text-accent font-display">{sig.tp1}</p>
                </div>
                <div>
                  <p className="text-muted text-xs font-display">PROVIDER</p>
                  <p className="text-text text-xs">{sig.provider}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-muted text-xs font-display">
                  {sig.timestamp ? new Date(sig.timestamp).toLocaleTimeString() : ''}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
