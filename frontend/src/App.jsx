import { useEffect, useState } from 'react'
import { AuditTerminal } from './components/AuditTerminal'
import { ChatInterface } from './components/ChatInterface'
import { SuccessOverlay } from './components/SuccessOverlay'

const createEntry = (step, detail, status = 'pending') => ({
  step,
  detail,
  status,
})

const initialAuditEntries = [
  createEntry('Semantic Match', 'Waiting for product intent resolution.', 'pending'),
  createEntry('Base Price Check', 'Awaiting the negotiated offer.', 'pending'),
  createEntry('Min Price Check', 'Waiting for the seller guardrail outcome.', 'pending'),
]

const getSettledAuditEntry = () => {
  const fallback = { order_id: 'Order unavailable', total_amount: 0 }
  let activeOrder = fallback
  try {
    activeOrder = { ...fallback, ...JSON.parse(window.localStorage.getItem('nexuspay_active_order') || '{}') }
  } catch {
    activeOrder = fallback
  }
  const paymentId = new URLSearchParams(window.location.search).get('razorpay_payment_id') || 'Payment ID unavailable'
  return {
    step: 'TRANSACTION_SETTLED',
    status: 'success',
    detail: `Payment (${paymentId}) confirmed via Razorpay for order ${activeOrder.order_id} (₹${Number(activeOrder.total_amount).toLocaleString('en-IN')}). Mandate authorization finalized.`,
  }
}

function App() {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'agent',
      text: 'I can resolve your product request and negotiate a price. Try: “I need a gaming keyboard for ₹3,200.”',
    },
  ])
  const [auditEntries, setAuditEntries] = useState(() => {
    try {
      const storedEntries = window.localStorage.getItem('nexuspay_audit_traces')
        ?? window.localStorage.getItem('nexuspay-audit-entries')
      return storedEntries ? JSON.parse(storedEntries) : initialAuditEntries
    } catch {
      return initialAuditEntries
    }
  })
  const [isSuccess, setIsSuccess] = useState(window.location.pathname === '/success')

  useEffect(() => {
    window.localStorage.setItem('nexuspay-audit-entries', JSON.stringify(auditEntries))
    window.localStorage.setItem('nexuspay_audit_traces', JSON.stringify(auditEntries))
  }, [auditEntries])

  const resetToInitialState = () => {
    setMessages([{
      id: 'welcome',
      sender: 'agent',
      text: 'I can resolve your product request and negotiate a price. Try: “I need a gaming keyboard for ₹3,200.”',
    }])
    setAuditEntries(initialAuditEntries)
    setIsSuccess(false)
    window.localStorage.removeItem('nexuspay_active_order')
    window.localStorage.removeItem('nexuspay_audit_traces')
    window.localStorage.removeItem('nexuspay-audit-entries')
    window.history.replaceState({}, '', '/')
  }

  const viewOrderHistory = () => {
    window.location.assign('/orders')
  }

  const visibleAuditEntries = isSuccess
    ? [...auditEntries, getSettledAuditEntry()]
    : auditEntries

  return (
    <main className="min-h-screen bg-slate-50 font-sans antialiased text-slate-800">
      <header className="border-b border-slate-200 bg-white px-8 py-4">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <a
              href="/"
              onClick={(event) => {
                event.preventDefault()
                resetToInitialState()
              }}
              aria-label="Go to NexusPay home"
              className="flex items-center text-2xl font-extrabold tracking-tight"
            >
              <span className="text-slate-800">Nexus</span>
              <span className="text-blue-600">Pay</span>
            </a>
          </div>

          <div className="flex items-center gap-4">
            <span className="hidden text-sm font-medium text-slate-500 sm:inline">
              AI Commerce Negotiation Console
            </span>
            <div className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs font-medium text-emerald-700 shadow-sm">
              Live Negotiation
            </div>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-7xl px-6 py-8">
        <div className="grid gap-8 lg:grid-cols-[1.55fr_1fr]">
          {isSuccess ? (
            <SuccessOverlay onStartNewNegotiation={resetToInitialState} onViewOrderHistory={viewOrderHistory} />
          ) : (
            <ChatInterface
              messages={messages}
              setMessages={setMessages}
              auditEntries={auditEntries}
              setAuditEntries={setAuditEntries}
              initialAuditEntries={initialAuditEntries}
            />
          )}
          <AuditTerminal entries={visibleAuditEntries} />
        </div>
      </div>
    </main>
  )
}

export default App
