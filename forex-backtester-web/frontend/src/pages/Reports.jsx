import { useState, useEffect } from 'react'
import { api } from '../utils/api'
import { useSession } from '../hooks/useSession'
import { StatCard, Button, SectionTitle, Badge, Card } from '../components/UI'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine, Cell } from 'recharts'
import { Download, RefreshCw } from 'lucide-react'

const TOOLTIP_STYLE = {
  backgroundColor: '#1A2235', border: '1px solid #1E2D45',
  borderRadius: 8, fontSize: 12, fontFamily: 'DM Mono',
}

export default function Reports() {
  const { session } = useSession()
  const [stats, setStats]     = useState(null)
  const [trades, setTrades]   = useState([])
  const [loading, setLoading] = useState(false)
  const [filterPair, setFilterPair] = useState('')
  const [activeTab, setActiveTab]   = useState('overview') // overview | trades | pairs | providers

  useEffect(() => { loadData() }, [session])

  async function loadData() {
    setLoading(true)
    const [s, t] = await Promise.all([
      api.getStats(session, filterPair || undefined).catch(() => null),
      api.getTrades(session).catch(() => []),
    ])
    setStats(s); setTrades(t)
    setLoading(false)
  }

  const overall = stats?.overall || {}
  const perPair = stats?.per_pair || {}
  const perProv = stats?.per_provider || {}

  const equityData = (overall.equity_curve || []).map((v, i) => ({ i, pips: v }))
  const pairData   = Object.entries(perPair).map(([pair, s]) => ({ pair, pips: s.total_pips, wr: s.win_rate }))

  const TABS = ['overview', 'trades', 'pairs', 'providers']

  return (
    <div className="p-8 animate-fade-in">
      <div className="flex items-center justify-between mb-8">
        <div>
          <p className="text-xs font-display text-muted uppercase tracking-widest mb-1">Analytics</p>
          <h1 className="text-2xl font-display text-text">Reports</h1>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={loadData} loading={loading}>
            <RefreshCw size={13} /> Refresh
          </Button>
          <Button variant="secondary" onClick={() => api.exportCsv(session)}>
            <Download size={13} /> Export CSV
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-surface border border-border rounded-lg p-1 w-fit">
        {TABS.map(t => (
          <button key={t} onClick={() => setActiveTab(t)}
            className={`px-4 py-1.5 rounded text-xs font-display uppercase tracking-widest transition-all ${
              activeTab === t ? 'bg-card text-accent' : 'text-muted hover:text-text'
            }`}>{t}</button>
        ))}
      </div>

      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Stat cards */}
          <div className="grid grid-cols-4 gap-4">
            <StatCard label="Win Rate"       value={`${overall.win_rate ?? '—'}%`}  color="green" />
            <StatCard label="Total Pips"     value={overall.total_pips != null ? `${overall.total_pips > 0 ? '+' : ''}${overall.total_pips}` : '—'} color={overall.total_pips >= 0 ? 'green' : 'red'} />
            <StatCard label="Profit Factor"  value={overall.profit_factor ?? '—'}   color="gold" />
            <StatCard label="RR Ratio"       value={overall.rr_ratio ?? '—'}        color="gold" />
            <StatCard label="Total Trades"   value={overall.total_trades ?? '—'}    />
            <StatCard label="Max Drawdown"   value={overall.max_drawdown_pips != null ? `${overall.max_drawdown_pips} pips` : '—'} color="red" />
            <StatCard label="Max Consec. L"  value={overall.max_consecutive_losses ?? '—'} color="red" />
            <StatCard label="Total USD"      value={overall.total_usd != null ? `$${overall.total_usd.toLocaleString()}` : '—'} color={overall.total_usd >= 0 ? 'green' : 'red'} />
          </div>

          {/* Equity curve */}
          {equityData.length > 0 && (
            <Card>
              <p className="text-xs font-display text-muted uppercase tracking-widest mb-4">Equity Curve (Pips)</p>
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={equityData}>
                  <XAxis dataKey="i" hide />
                  <YAxis domain={['auto', 'auto']} tick={{ fill: '#6B7A99', fontSize: 11 }} width={50} />
                  <Tooltip contentStyle={TOOLTIP_STYLE} formatter={v => [`${v} pips`, 'Equity']} />
                  <ReferenceLine y={0} stroke="#1E2D45" />
                  <Line type="monotone" dataKey="pips" stroke="#00D4AA" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </Card>
          )}
        </div>
      )}

      {activeTab === 'trades' && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-muted font-display text-xs uppercase tracking-widest border-b border-border">
                <th className="pb-3 pr-4">Pair</th>
                <th className="pb-3 pr-4">Dir</th>
                <th className="pb-3 pr-4">Outcome</th>
                <th className="pb-3 pr-4">Entry</th>
                <th className="pb-3 pr-4">Exit</th>
                <th className="pb-3 pr-4">Pips</th>
                <th className="pb-3 pr-4">USD P&L</th>
                <th className="pb-3">Provider</th>
              </tr>
            </thead>
            <tbody>
              {trades.slice(0, 200).map((t, i) => (
                <tr key={i} className="border-b border-border/50 hover:bg-card/50 transition-colors">
                  <td className="py-2.5 pr-4 font-display text-text">{t.pair}</td>
                  <td className="py-2.5 pr-4">
                    <Badge variant={t.direction === 'BUY' ? 'win' : 'loss'}>{t.direction}</Badge>
                  </td>
                  <td className="py-2.5 pr-4">
                    <Badge variant={t.outcome?.toLowerCase()}>{t.outcome}</Badge>
                  </td>
                  <td className="py-2.5 pr-4 font-display text-muted">{t.entry_price?.toFixed(4)}</td>
                  <td className="py-2.5 pr-4 font-display text-muted">{t.exit_price?.toFixed(4) ?? '—'}</td>
                  <td className={`py-2.5 pr-4 font-display ${t.pips >= 0 ? 'text-accent' : 'text-red'}`}>
                    {t.pips != null ? `${t.pips > 0 ? '+' : ''}${t.pips}` : '—'}
                  </td>
                  <td className={`py-2.5 pr-4 font-display ${t.usd_pnl >= 0 ? 'text-accent' : 'text-red'}`}>
                    {t.usd_pnl != null ? `$${t.usd_pnl > 0 ? '+' : ''}${t.usd_pnl}` : '—'}
                  </td>
                  <td className="py-2.5 text-muted text-xs">{t.provider}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {trades.length === 0 && (
            <p className="text-center text-muted py-12 text-sm">No trades yet. Run a backtest first.</p>
          )}
        </div>
      )}

      {activeTab === 'pairs' && (
        <div className="space-y-6">
          {pairData.length > 0 && (
            <Card>
              <p className="text-xs font-display text-muted uppercase tracking-widest mb-4">Pips by Pair</p>
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={pairData}>
                  <XAxis dataKey="pair" tick={{ fill: '#6B7A99', fontSize: 11 }} />
                  <YAxis tick={{ fill: '#6B7A99', fontSize: 11 }} />
                  <Tooltip contentStyle={TOOLTIP_STYLE} />
                  <ReferenceLine y={0} stroke="#1E2D45" />
                  <Bar dataKey="pips" radius={[4, 4, 0, 0]}>
                    {pairData.map((entry, i) => (
                      <Cell key={i} fill={entry.pips >= 0 ? '#00D4AA' : '#FF4D6D'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Card>
          )}
          <div className="grid grid-cols-2 gap-4">
            {Object.entries(perPair).map(([pair, s]) => (
              <Card key={pair}>
                <p className="text-text font-display font-medium mb-3">{pair}</p>
                <div className="grid grid-cols-3 gap-3 text-sm">
                  <div><p className="text-muted text-xs">Win Rate</p><p className="text-accent font-display">{s.win_rate}%</p></div>
                  <div><p className="text-muted text-xs">Pips</p><p className={`font-display ${s.total_pips >= 0 ? 'text-accent' : 'text-red'}`}>{s.total_pips > 0 ? '+' : ''}{s.total_pips}</p></div>
                  <div><p className="text-muted text-xs">Trades</p><p className="text-text font-display">{s.total_trades}</p></div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'providers' && (
        <div className="grid grid-cols-2 gap-4">
          {Object.entries(perProv).map(([prov, s]) => (
            <Card key={prov}>
              <p className="text-text font-display font-medium mb-3">{prov}</p>
              <div className="grid grid-cols-3 gap-3 text-sm">
                <div><p className="text-muted text-xs">Win Rate</p><p className="text-accent font-display">{s.win_rate}%</p></div>
                <div><p className="text-muted text-xs">Pips</p><p className={`font-display ${s.total_pips >= 0 ? 'text-accent' : 'text-red'}`}>{s.total_pips > 0 ? '+' : ''}{s.total_pips}</p></div>
                <div><p className="text-muted text-xs">PF</p><p className="text-gold font-display">{s.profit_factor}</p></div>
                <div><p className="text-muted text-xs">Trades</p><p className="text-text font-display">{s.total_trades}</p></div>
                <div><p className="text-muted text-xs">RR</p><p className="text-text font-display">{s.rr_ratio}</p></div>
                <div><p className="text-muted text-xs">Max DD</p><p className="text-red font-display">{s.max_drawdown_pips}p</p></div>
              </div>
            </Card>
          ))}
          {Object.keys(perProv).length === 0 && (
            <p className="col-span-2 text-center text-muted py-12 text-sm">No provider data yet.</p>
          )}
        </div>
      )}
    </div>
  )
}
