import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { SessionProvider } from './hooks/useSession'
import Sidebar      from './components/Sidebar'
import Setup        from './pages/Setup'
import Channels     from './pages/Channels'
import Backtest     from './pages/Backtest'
import LiveMonitor  from './pages/LiveMonitor'
import Reports      from './pages/Reports'
import './index.css'

export default function App() {
  return (
    <SessionProvider>
      <BrowserRouter>
        <div className="flex min-h-screen">
          <Sidebar />
          <main className="flex-1 overflow-y-auto">
            <Routes>
              <Route path="/"          element={<Navigate to="/setup" replace />} />
              <Route path="/setup"     element={<Setup />} />
              <Route path="/channels"  element={<Channels />} />
              <Route path="/backtest"  element={<Backtest />} />
              <Route path="/live"      element={<LiveMonitor />} />
              <Route path="/reports"   element={<Reports />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </SessionProvider>
  )
}
