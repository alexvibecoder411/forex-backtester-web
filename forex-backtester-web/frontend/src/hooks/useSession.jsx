import { createContext, useContext, useState, useEffect } from 'react'
import { api } from '../utils/api'

const SessionCtx = createContext(null)

export function SessionProvider({ children }) {
  const [session, setSession]     = useState(() => localStorage.getItem('session_name') || 'default')
  const [connected, setConnected] = useState(false)
  const [userName, setUserName]   = useState(null)
  const [userId, setUserId]       = useState(null)
  const [checking, setChecking]   = useState(true)

  useEffect(() => {
    api.authStatus(session)
      .then(r => { setConnected(r.connected); setUserName(r.name || null) })
      .catch(() => setConnected(false))
      .finally(() => setChecking(false))
  }, [session])

  const saveSession = (name) => {
    localStorage.setItem('session_name', name)
    setSession(name)
  }

  return (
    <SessionCtx.Provider value={{ session, saveSession, connected, setConnected, userName, setUserName, userId, setUserId, checking }}>
      {children}
    </SessionCtx.Provider>
  )
}

export const useSession = () => useContext(SessionCtx)
