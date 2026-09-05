import { useEffect, useState } from 'react'

const initialGreeting = {
  id: 'welcome',
  sender: 'agent',
  text: 'I can resolve your product request and negotiate a price. Try: “I need a gaming keyboard for ₹3,200.”',
}

export function ChatInterface({ messages, setMessages, setAuditEntries, initialAuditEntries }) {
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [upsellNotice, setUpsellNotice] = useState('')
  const [upsellAddedMessageId, setUpsellAddedMessageId] = useState(null)

  useEffect(() => {
    window.localStorage.removeItem('nexuspay_audit_traces')
    window.localStorage.removeItem('nexuspay-audit-entries')
    window.localStorage.removeItem('nexuspay_active_order')
    setAuditEntries(initialAuditEntries)
    setMessages([initialGreeting])
    setUpsellNotice('')
    setUpsellAddedMessageId(null)
  }, [])

  const persistActiveOrder = (activeOrder) => {
    window.localStorage.setItem('nexuspay_active_order', JSON.stringify(activeOrder))
  }

  const updateAudit = (result) => {
    setAuditEntries((current) => {
      if (result?.audit?.step === 'DOMAIN_GUARDRAIL') {
        const traces = result.traces ?? [{
          step: 'DOMAIN_GUARDRAIL',
          status: 'blocked',
          detail: result.audit.details,
        }]
        const incomingSteps = new Set(traces.map((trace) => trace.step))
        const historicalEntries = current.filter(
          (entry) => !(entry.status === 'pending' && !entry.traceId && incomingSteps.has(entry.step)),
        )
        return [
          ...historicalEntries,
          ...traces.map((trace) => ({
            ...trace,
            traceId: crypto.randomUUID(),
            timestamp: new Date().toISOString(),
          })),
        ]
      }

      const incomingTraces = Array.isArray(result?.traces) ? result.traces : []
      const incomingSteps = new Set(incomingTraces.map((trace) => trace.step))
      const next = [
        ...current.filter(
          (entry) => !(entry.status === 'pending' && !entry.traceId && incomingSteps.has(entry.step)),
        ),
        ...incomingTraces.map((trace) => ({
          ...trace,
          traceId: crypto.randomUUID(),
          timestamp: new Date().toISOString(),
        })),
      ]

      const mandate = result?.intent_mandate ?? result?.order?.intent_mandate
      const auditRecords = [
        result?.order?.audit_record,
        result?.upsell_audit,
        result?.provider_used
          ? {
              step: 'LLM_ROUTER_BENCHMARK',
              details: `${result.provider_used} responded with ${result.model_used} in ${result.latency_seconds}s.`,
            }
          : null,
        mandate
          ? {
              step: 'MANDATE_GENERATED',
              details: `AP2 permission receipt generated for ${result.order?.order_id ?? mandate.order_id} using ACP-v1.0.`,
            }
          : null,
      ].filter(Boolean)

      auditRecords.forEach((record) => {
        const entry = {
          step: record.step,
          status: 'success',
          detail: record.details ?? record.detail ?? 'Mandate recorded.',
          traceId: crypto.randomUUID(),
          timestamp: new Date().toISOString(),
        }
        next.push(entry)
      })

      return next
    })
  }

  const handleAddToOrder = async (message) => {
    if (!message?.order || !message?.upsell || !message.productId) {
      return
    }

    try {
      const response = await fetch('http://127.0.0.1:8011/api/v1/checkout-combo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          primary_product_id: message.productId,
          primary_agreed_price: message.order.amount,
          upsell_product_id: message.upsell.itemId,
        }),
      })

      const payload = await response.json()
      if (!response.ok) {
        setUpsellNotice(payload.detail || 'Combo checkout was rejected by the dynamic guardrail.')
        setAuditEntries((current) => [
          ...current,
          {
            step: 'COMBO_GUARDRAIL_FAILED',
            status: 'blocked',
            detail: payload.detail || 'Combo guardrail rejected the addon bundle.',
          },
        ])
        return
      }

      setMessages((current) =>
        current.map((currentMessage) =>
          currentMessage.id === message.id
            ? {
                ...currentMessage,
                order: {
                  ...currentMessage.order,
                  order_id: payload.order_id,
                  payment_url: payload.payment_url ?? currentMessage.order.payment_url,
                  intent_mandate: payload.intent_mandate,
                },
              }
            : currentMessage,
        ),
      )

      setUpsellAddedMessageId(message.id)
      persistActiveOrder({
        product_id: message.productId,
        order_id: payload.order_id,
        items: payload.items,
        total_amount: payload.total_amount,
      })
      setUpsellNotice(payload.message)
      setAuditEntries((current) => {
        const next = [...current]
        const comboIndex = next.findIndex((entry) => entry.step === 'COMBO_GUARDRAIL_PASSED')
        const orderIndex = next.findIndex((entry) => entry.step === 'ORDER_UPDATED')

        const comboEntry = {
          step: 'COMBO_GUARDRAIL_PASSED',
          status: 'success',
          detail: `Combo minimum guardrail passed: ₹${payload.total_amount.toLocaleString('en-IN')} total meets the floor.`,
          traceId: crypto.randomUUID(),
          timestamp: new Date().toISOString(),
        }
        const orderEntry = {
          step: 'ORDER_UPDATED',
          status: 'success',
          detail: `Razorpay order updated to new combo total ₹${payload.total_amount.toLocaleString('en-IN')} (Order ID: ${payload.order_id}).`,
          traceId: crypto.randomUUID(),
          timestamp: new Date().toISOString(),
        }

        if (comboIndex >= 0) next[comboIndex] = comboEntry
        else next.push(comboEntry)

        if (orderIndex >= 0) next[orderIndex] = orderEntry
        else next.push(orderEntry)

        return next
      })
    } catch {
      setUpsellNotice('Unable to finalize the combo order right now.')
    }
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    const trimmed = input.trim()
    if (!trimmed || isLoading) {
      return
    }

    const activeOrder = (() => {
      try {
        const storedOrder = window.localStorage.getItem('nexuspay_active_order')
        return storedOrder ? JSON.parse(storedOrder) : null
      } catch {
        return null
      }
    })()
    const chatHistory = messages.map((message) => ({
      role: message.sender === 'agent' ? 'assistant' : 'user',
      content: message.text,
    }))
    const buyerMessage = { id: crypto.randomUUID(), sender: 'user', text: trimmed }
    setMessages((current) => [...current, buyerMessage])
    setInput('')
    setUpsellNotice('')
    setUpsellAddedMessageId(null)
    setIsLoading(true)

    try {
      const response = await fetch('http://127.0.0.1:8011/api/v1/semantic-negotiation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: trimmed, chat_history: chatHistory, active_order: activeOrder }),
      })

      const payload = await response.json()
      if (!response.ok) {
        const agentReply = {
          id: crypto.randomUUID(),
          sender: 'agent',
          text: payload.detail || 'The negotiation was blocked by the seller guardrail.',
        }
        setMessages((current) => [...current, agentReply])
        updateAudit({ negotiation: { agreed: false, message_to_buyer: agentReply.text } })
        return
      }

      const currentOrder = payload.success === false || !payload.order ? null : payload.order
      const currentUpsell = currentOrder && payload.upsell_pitch
        ? {
            pitch: payload.upsell_pitch,
            itemId: payload.upsell_item_id,
            price: payload.upsell_price,
          }
        : null
      if (!currentOrder) {
        if (payload.active_order?.product_id) {
          persistActiveOrder(payload.active_order)
        }
      }

      const agentReply = {
        id: crypto.randomUUID(),
        sender: 'agent',
        text: payload.negotiation.message_to_buyer,
        productId: payload.product_id,
        addonAccepted: payload.addon_accepted === true,
        order: currentOrder,
        upsell: payload.addon_accepted === true ? currentUpsell : null,
      }
      if (currentOrder) {
        persistActiveOrder({
          product_id: payload.product_id,
          order_id: currentOrder.order_id,
          items: [{ name: currentOrder.product_name, price: currentOrder.amount }],
          total_amount: currentOrder.amount,
        })
      }
      setMessages((current) => [...current, agentReply])
      updateAudit(payload)
    } catch {
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          sender: 'agent',
          text: 'Unable to reach the NexusPay backend. Please ensure the FastAPI server is running.',
        },
      ])
      setAuditEntries((current) =>
        current.map((entry) => ({
          ...entry,
          status: 'blocked',
          detail: 'Request failed; the backend is unavailable.',
        })),
      )
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <section className="flex min-h-[620px] flex-col overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-lg shadow-slate-200/50">
      <div className="border-b border-slate-100 px-5 py-4">
        <h2 className="text-lg font-semibold text-slate-800">Chat Interface</h2>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto bg-slate-50/80 px-4 py-4">
        {messages.map((message) => {
          const isUpsellAdded = upsellAddedMessageId === message.id
          const finalAmount = isUpsellAdded && message.upsell
            ? message.order.amount + message.upsell.price
            : message.order?.amount

          return (
          <div
            key={message.id}
            className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div className="max-w-[80%] space-y-3">
              <div
                className={`rounded-2xl px-4 py-3 text-sm leading-6 shadow-sm ${
                message.sender === 'user'
                  ? 'rounded-br-none bg-blue-600 text-white'
                  : 'rounded-bl-none bg-slate-100 text-slate-800'
                }`}
              >
                {message.text}
              </div>

              {message.order && (
                <div className="rounded-2xl border border-blue-200 bg-blue-50 p-4 shadow-sm">
                  <div className="mb-2 flex items-center justify-between gap-3">
                    <span className="text-sm font-semibold text-slate-900">Pay via Razorpay</span>
                    <span className="rounded-full bg-emerald-100 px-2 py-1 text-xs font-semibold text-emerald-700">
                      ₹{finalAmount.toLocaleString('en-IN')}
                    </span>
                  </div>
                  <p className="mb-1 text-xs text-slate-600">{message.order.product_name}</p>
                  {message.order.order_id && (
                    <p className="mb-3 text-[11px] font-medium text-slate-500">Order ID: {message.order.order_id}</p>
                  )}
                  {message.upsell && message.addonAccepted && (
                    <div className="mb-3 rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
                      <p className="font-medium">{message.upsell.pitch}</p>
                    </div>
                  )}
                  {message.order?.intent_mandate && (
                    <div className="mb-3 rounded-xl border border-cyan-200 bg-cyan-50 p-3 text-xs text-cyan-900">
                      <div className="mb-2 flex items-center justify-between gap-2">
                        <span className="font-semibold uppercase tracking-[0.18em] text-cyan-700">AP2 Intent Mandate</span>
                        <span className="rounded-full bg-cyan-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.14em] text-cyan-700">
                          {message.order.intent_mandate.protocol}
                        </span>
                      </div>
                      <p className="mb-1">
                        <span className="font-semibold">Authorized amount:</span> ₹{(message.order.intent_mandate.total_amount_paise / 100).toLocaleString('en-IN')}
                      </p>
                      <p className="mb-1 break-all">
                        <span className="font-semibold">Signature:</span> {message.order.intent_mandate.cryptographic_signature}
                      </p>
                      <p className="break-all text-[10px] text-cyan-800">
                        {message.order.intent_mandate.mandate_id} • {message.order.intent_mandate.timestamp}
                      </p>
                    </div>
                  )}
                  <div className="flex flex-col gap-2 sm:flex-row">
                    {message.upsell && message.addonAccepted && (
                      <button
                        type="button"
                        onClick={() => handleAddToOrder(message)}
                        disabled={isUpsellAdded}
                        className="rounded-xl border border-amber-300 bg-amber-100 px-4 py-2.5 text-center text-sm font-semibold text-amber-900 transition hover:bg-amber-200 disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        {isUpsellAdded
                          ? 'Added to Cart ✅'
                          : `Add to Order (₹${message.upsell.price.toLocaleString('en-IN')})`}
                      </button>
                    )}
                    <a
                      href={message.order.payment_url}
                      target="_blank"
                      rel="noreferrer"
                      className="flex-1 rounded-xl bg-blue-600 px-4 py-2.5 text-center text-sm font-semibold text-white transition hover:bg-blue-700"
                    >
                      Pay ₹{finalAmount.toLocaleString('en-IN')} via Razorpay
                    </a>
                  </div>
                  {message.upsell && message.addonAccepted && upsellNotice && (
                    <p className="mt-2 text-xs font-medium text-amber-800">{upsellNotice}</p>
                  )}
                </div>
              )}
            </div>
          </div>
          )
        })}

        {isLoading && (
          <div className="flex justify-start">
            <div className="rounded-2xl rounded-bl-none border border-slate-200 bg-slate-100 px-4 py-3 text-sm text-slate-600">
              Negotiating with the seller agent...
            </div>
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="border-t border-slate-100 bg-white p-4">
        <div className="flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Example: I need a gaming keyboard for ₹3,200"
            className="flex-1 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-800 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
          />
          <button
            type="submit"
            disabled={isLoading}
            className="rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isLoading ? 'Sending...' : 'Send'}
          </button>
        </div>
      </form>
    </section>
  )
}
