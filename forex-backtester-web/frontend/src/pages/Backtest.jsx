import { useState, useEffect, useRef } from 'react'
import { api } from '../utils/api'
import { useSession } from '../hooks/useSession'
import { Card, Input, Select, Button, SectionTitle, Progress } from '../components/UI'
import { Download, Play, RefreshCw } from 'lucide-react'

export default function Backtest() {
  const { session } = useSession()
  const [fetchDays, setFetchDays]   = useState(180)
  const [lotSize, setLotSize]       = useState(0.1)
  const [beMoveAfterTp1, setBe]     = useState(true)
  const [tpSplit, setTpSplit]       = useState('equal')
  const [filterPair, setFilterPair] = useState('')
  const [job, setJob]               = useState(null)
  const [phase, setPhase]           = useState(null) // null | fetch | run
  const [log, setLog]               = useState([])
  const pollRef                     = useRef(null)
  const logRef                      = useRef(null)

  function pushLog(msg) {
    setLog(l => [...l.slice(-49), msg])
    setTimeout(() => logRef.current?.scrollTo(0, 99999), 50)
  }

  function startPoll(jobId, onDone) {
    if (pollRef.current) clearInterval(pollRef.current)
    pollRef.current = setInterval(async () => {
      const j = await api.jobStatus(jobId).catch(() => null)
      if (!j) return
      setJob(j)
      if (j.message) pushLog(j.message)
      if (j.status === 'done' || j.status === 'error') {
        clearInterval(pollRef.current)
        onDone?.(j)
      }
    }, 1200)
  }

  async function handleFetch() {
    setPhase('fetch'); setLog([])
    pushLog('Starting historical fetch...')
    const { job_id } = await api.fetchHistory({ session_name: session, history_days: fetchDays })
    startPoll(job_id, () => setPhase(null))
  }

  async function handleRun() {
    setPhase('run'); setLog([])
    pushLog('Starting simulation...')
    const { job_id } = await api.runBacktest({
      session_name:  session,
      lot_size:      parseFloat(lotSize),
      be_after_tp1:  beMoveAfterTp1,
      tp_split:      tpSplit,
      pair:          filterPair || undefined,
      history_days:  fetchDays,
    })
    startPoll(job_id, () => setPhase(null))
  }

  const running = phase !== null
  const pct = job && job.total > 0 ? Math.round((job.progress / job.total) * 100) : 0

  return (
    <div className="p-8 max-w-2xl animate-fade-in">
      <SectionTitle>Simulation</SectionTitle>
      <h1 className="text-2xl font-display text-text mb-1">Backtest</h1>
      <p className="text-muted text-sm mb-8">Fetch historical signals and simulate trades against real OHLC data.</p>

      {/* Step 1 */}
      <Card className="mb-4">
        <p className="text-xs font-display text-accent uppercase tracking-widest mb-4">Step 1 — Fetch Signals</p>
        <div className="flex items-end gap-4">
          <div className="flex-1">
            <Input label="History (days)" type="number" value={fetchDays}
              onChange={e => setFetchDays(Number(e.target.value))} />
          </div>
          <Button onClick={handleFetch} loading={phase === 'fetch'} disabled={running}>
            <Download size={14} /> Fetch from Telegram
          </Button>
        </div>
      </Card>

      {/* Step 2 */}
      <Card className="mb-6">
        <p className="text-xs font-display text-accent uppercase tracking-widest mb-4">Step 2 — Configure & Run</p>
        <div className="grid grid-cols-2 gap-4 mb-4">
          <Input label="Lot Size" type="number" step="0.01" value={lotSize}
            onChange={e => setLotSize(e.target.value)} />
          <Input label="Filter by Pair (optional)" value={filterPair}
            onChange={e => setFilterPair(e.target.value)} placeholder="XAUUSD" />
          <Select label="TP Split" value={tpSplit} onChange={e => setTpSplit(e.target.value)}>
            <option value="equal">Equal split</option>
            <option value="custom">Custom ratios</option>
          </Select>
          <Select label="Breakeven After TP1" value={beMoveAfterTp1 ? 'yes' : 'no'}
            onChange={e => setBe(e.target.value === 'yes')}>
            <option value="yes">Yes</option>
            <option value="no">No</option>
          </Select>
        </div>
        <Button onClick={handleRun} loading={phase === 'run'} disabled={running}>
          <Play size={14} /> Run Simulation
        </Button>
      </Card>

      {/* Progress */}
      {job && (
        <Card>
          <div className="flex items-center justify-between mb-3">
            <p className="text-xs font-display text-muted uppercase tracking-widest">Progress</p>
            <span className={`text-xs font-display ${
              job.status === 'done' ? 'text-accent' :
              job.status === 'error' ? 'text-red' : 'text-gold'
            }`}>{job.status.toUpperCase()}</span>
          </div>
          <Progress value={job.progress} total={job.total || 1} />
          <div
            ref={logRef}
            className="mt-4 h-32 overflow-y-auto bg-surface rounded-lg p-3 space-y-1"
          >
            {log.map((l, i) => (
              <p key={i} className="text-xs font-display text-muted">{l}</p>
            ))}
          </div>
          {job.status === 'done' && (
            <p className="text-accent text-sm mt-3 font-display">
              ✓ Done. Head to Reports to see results.
            </p>
          )}
        </Card>
      )}
    </div>
  )
}
