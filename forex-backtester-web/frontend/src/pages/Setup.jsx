import { useState } from 'react'
import { api } from '../utils/api'
import { useSession } from '../hooks/useSession'
import { Card, Input, Button, SectionTitle, Dot } from '../components/UI'
import { CheckCircle, AlertCircle } from 'lucide-react'

export default function Setup() {
  const { session, saveSession, connected, setConnected, setUserName } = useSession()

  const [form, setForm]       = useState({ api_id: '', api_hash: '', phone: '', session_name: session })
  const [code, setCode]       = useState('')
  const [password, setPassword] = useState('')
  const [step, setStep]       = useState(connected ? 'connected' : 'idle') // idle | code | 2fa | connected
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState(null)

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  async function handleConnect() {
    setLoading(true); setError(null)
    try {
      saveSession(form.session_name)
      const res = await api.connect(form)
      if (res.status === 'connected') {
        setConnected(true); setUserName(res.name); setStep('connected')
      } else {
        setStep('code')
      }
    } catch (e) { setError(e.message) }
    finally { setLoading(false) }
  }

  async function handleVerify() {
    setLoading(true); setError(null)
    try {
      const res = await api.verify({ session_name: form.session_name, phone: form.phone, code, password })
      if (res.status === 'connected') {
        setConnected(true); setUserName(res.name); setStep('connected')
      } else if (res.status === '2fa_required') {
        setStep('2fa')
      }
    } catch (e) { setError(e.message) }
    finally { setLoading(false) }
  }

  async function handleDisconnect() {
    await api.disconnect({ session_name: form.session_name })
    setConnected(false); setStep('idle')
  }

  return (
    <div className="p-8 max-w-xl animate-fade-in">
      <SectionTitle>Telegram Setup</SectionTitle>
      <h1 className="text-2xl font-display text-text mb-1">Connect Your Account</h1>
      <p className="text-muted text-sm mb-8">
        Enter your Telegram API credentials to start pulling signals.
        Get them from{' '}
        <a href="https://my.telegram.org/apps" target="_blank" className="text-accent hover:underline">
          my.telegram.org/apps
        </a>
      </p>

      {step === 'connected' ? (
        <Card>
          <div className="flex items-center gap-3 mb-4">
            <CheckCircle size={20} className="text-accent" />
            <div>
              <p className="text-text font-medium">Connected to Telegram</p>
              <p className="text-muted text-sm">Session: {form.session_name}</p>
            </div>
          </div>
          <Button variant="danger" onClick={handleDisconnect}>Disconnect</Button>
        </Card>
      ) : step === 'code' || step === '2fa' ? (
        <Card>
          <p className="text-text mb-4 text-sm">
            {step === 'code'
              ? '📱 A verification code was sent to your Telegram app. Enter it below.'
              : '🔐 Two-factor authentication required. Enter your password.'}
          </p>
          <div className="space-y-4">
            {step === 'code' && (
              <Input label="Verification Code" value={code}
                onChange={e => setCode(e.target.value)} placeholder="12345" />
            )}
            {(step === '2fa') && (
              <Input label="2FA Password" type="password" value={password}
                onChange={e => setPassword(e.target.value)} placeholder="Your 2FA password" />
            )}
            {error && (
              <div className="flex items-center gap-2 text-red text-sm">
                <AlertCircle size={14} />{error}
              </div>
            )}
            <Button onClick={handleVerify} loading={loading}>Verify & Connect</Button>
          </div>
        </Card>
      ) : (
        <Card>
          <div className="space-y-4">
            <Input label="Session Name" value={form.session_name}
              onChange={e => set('session_name', e.target.value)}
              placeholder="default" />
            <Input label="API ID" value={form.api_id}
              onChange={e => set('api_id', e.target.value)}
              placeholder="12345678" />
            <Input label="API Hash" value={form.api_hash}
              onChange={e => set('api_hash', e.target.value)}
              placeholder="abc123..." />
            <Input label="Phone Number" value={form.phone}
              onChange={e => set('phone', e.target.value)}
              placeholder="+1234567890" />
            {error && (
              <div className="flex items-center gap-2 text-red text-sm">
                <AlertCircle size={14} />{error}
              </div>
            )}
            <Button onClick={handleConnect} loading={loading}>Connect to Telegram</Button>
          </div>
        </Card>
      )}

      <div className="mt-8 p-4 bg-surface border border-border rounded-xl">
        <p className="text-xs font-display text-muted uppercase tracking-widest mb-2">How to get credentials</p>
        <ol className="text-sm text-muted space-y-1 list-decimal list-inside">
          <li>Go to <span className="text-accent">my.telegram.org/apps</span></li>
          <li>Log in with your phone number</li>
          <li>Create a new application (any name)</li>
          <li>Copy the <span className="text-text">api_id</span> and <span className="text-text">api_hash</span></li>
        </ol>
      </div>
    </div>
  )
}
