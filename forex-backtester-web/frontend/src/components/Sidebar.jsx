import { NavLink } from 'react-router-dom'
import { Settings, Radio, Play, BarChart2, Layers, Wifi, WifiOff } from 'lucide-react'
import { useSession } from '../hooks/useSession'

const nav = [
  { to: '/setup',   icon: Settings,  label: 'Setup' },
  { to: '/channels',icon: Layers,    label: 'Channels' },
  { to: '/backtest',icon: Play,      label: 'Backtest' },
  { to: '/live',    icon: Radio,     label: 'Live' },
  { to: '/reports', icon: BarChart2, label: 'Reports' },
]

export default function Sidebar() {
  const { connected, userName } = useSession()

  return (
    <aside className="w-56 min-h-screen bg-surface border-r border-border flex flex-col">
      {/* Logo */}
      <div className="px-5 py-6 border-b border-border">
        <p className="font-display text-accent text-sm tracking-widest uppercase">FX Backtester</p>
        <p className="text-muted text-xs mt-0.5 font-display">Signal Intelligence</p>
      </div>

      {/* Nav */}
      <nav className="flex-1 p-3 space-y-0.5">
        {nav.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-150 ` +
              (isActive
                ? 'bg-accent/10 text-accent border border-accent/20'
                : 'text-muted hover:text-text hover:bg-card')
            }
          >
            <Icon size={15} />
            <span className="font-display">{label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Connection status */}
      <div className="p-4 border-t border-border">
        <div className="flex items-center gap-2">
          {connected
            ? <Wifi size={13} className="text-accent" />
            : <WifiOff size={13} className="text-muted" />}
          <span className="text-xs font-display text-muted">
            {connected ? (userName || 'Connected') : 'Disconnected'}
          </span>
        </div>
      </div>
    </aside>
  )
}
