import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

export function StatCard({ label, value, sub, trend, color }) {
  const colors = { green: 'text-accent', red: 'text-red', gold: 'text-gold', muted: 'text-muted' }
  return (
    <div className="bg-card border border-border rounded-xl p-5 animate-fade-in">
      <p className="text-muted text-xs font-display uppercase tracking-widest mb-2">{label}</p>
      <p className={`text-2xl font-display font-medium ${colors[color] || 'text-text'}`}>{value}</p>
      {sub && <p className="text-muted text-xs mt-1">{sub}</p>}
    </div>
  )
}

export function Badge({ children, variant = 'default' }) {
  const styles = {
    win:       'bg-accent/10 text-accent border border-accent/20',
    loss:      'bg-red/10 text-red border border-red/20',
    breakeven: 'bg-gold/10 text-gold border border-gold/20',
    pending:   'bg-muted/10 text-muted border border-border',
    default:   'bg-surface text-muted border border-border',
  }
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-display ${styles[variant] || styles.default}`}>
      {children}
    </span>
  )
}

export function Button({ children, onClick, variant = 'primary', disabled, loading, className = '' }) {
  const styles = {
    primary:   'bg-accent text-bg hover:bg-accent/90',
    secondary: 'bg-surface border border-border text-text hover:border-accent/40',
    danger:    'bg-red/10 border border-red/20 text-red hover:bg-red/20',
    ghost:     'text-muted hover:text-text',
  }
  return (
    <button
      onClick={onClick}
      disabled={disabled || loading}
      className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-150 disabled:opacity-40 disabled:cursor-not-allowed ${styles[variant]} ${className}`}
    >
      {loading && <span className="w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full animate-spin" />}
      {children}
    </button>
  )
}

export function Input({ label, ...props }) {
  return (
    <div>
      {label && <label className="block text-xs text-muted font-display uppercase tracking-widest mb-1.5">{label}</label>}
      <input
        {...props}
        className="w-full bg-surface border border-border text-text rounded-lg px-3 py-2 text-sm font-display placeholder:text-muted/50 focus:outline-none focus:border-accent/50 transition-colors"
      />
    </div>
  )
}

export function Select({ label, children, ...props }) {
  return (
    <div>
      {label && <label className="block text-xs text-muted font-display uppercase tracking-widest mb-1.5">{label}</label>}
      <select
        {...props}
        className="w-full bg-surface border border-border text-text rounded-lg px-3 py-2 text-sm font-display focus:outline-none focus:border-accent/50 transition-colors"
      >
        {children}
      </select>
    </div>
  )
}

export function Card({ children, className = '' }) {
  return (
    <div className={`bg-card border border-border rounded-xl p-6 ${className}`}>
      {children}
    </div>
  )
}

export function SectionTitle({ children }) {
  return (
    <h2 className="text-xs font-display uppercase tracking-widest text-muted mb-4">{children}</h2>
  )
}

export function Dot({ active }) {
  return (
    <span className={`inline-block w-2 h-2 rounded-full ${active ? 'bg-accent pulse-dot' : 'bg-muted'}`} />
  )
}

export function Progress({ value, total }) {
  const pct = total > 0 ? Math.round((value / total) * 100) : 0
  return (
    <div>
      <div className="flex justify-between text-xs text-muted mb-1">
        <span>{value} / {total}</span>
        <span>{pct}%</span>
      </div>
      <div className="h-1.5 bg-surface rounded-full overflow-hidden">
        <div
          className="h-full bg-accent transition-all duration-300 rounded-full"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}
