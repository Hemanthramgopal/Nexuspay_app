import { useState } from 'react'

const fallbackOrder = {
  order_id: 'Order unavailable',
  items: [{ name: 'Order details unavailable', price: 0 }],
  total_amount: 0,
}

const readActiveOrder = () => {
  try {
    const storedOrder = window.localStorage.getItem('nexuspay_active_order')
    return storedOrder ? { ...fallbackOrder, ...JSON.parse(storedOrder) } : fallbackOrder
  } catch {
    return fallbackOrder
  }
}

const readPaymentId = () => new URLSearchParams(window.location.search).get('razorpay_payment_id') || 'Payment ID unavailable'

export function SuccessOverlay({ onStartNewNegotiation, onViewOrderHistory }) {
  const [activeOrder] = useState(readActiveOrder)
  const [paymentId] = useState(readPaymentId)

  const formatPrice = (price) => `₹${Number(price).toLocaleString('en-IN')}`
  return (
    <div className="relative overflow-hidden rounded-2xl border border-emerald-400/30 bg-[#101b2f] p-6 shadow-2xl shadow-emerald-950/30 sm:p-8">
      <div className="pointer-events-none absolute inset-0 success-confetti" aria-hidden="true">
        {Array.from({ length: 18 }, (_, index) => <span key={index} />)}
      </div>

      <div className="relative text-center">
        <div className="success-check mx-auto mb-5 flex h-20 w-20 items-center justify-center rounded-full border border-emerald-300/50 bg-emerald-400 text-5xl font-bold text-[#102238] shadow-[0_0_42px_rgba(52,211,153,0.35)]">
          <span className="relative">✓<span className="success-sparkle">✦</span></span>
        </div>
        <p className="text-xs font-semibold uppercase tracking-[0.28em] text-emerald-300">Transaction settled</p>
        <h2 className="mt-2 text-3xl font-semibold tracking-tight text-white">Payment successful</h2>
        <p className="mt-2 text-sm text-slate-400">Your negotiated NexusPay order is confirmed.</p>
      </div>

      <div className="relative mt-8 overflow-hidden rounded-xl border border-slate-700 bg-[#0a1325]">
        <div className="border-b border-slate-700 px-4 py-3 text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">Order summary</div>
        <div className="divide-y divide-slate-800 px-4 text-sm">
          {activeOrder.items.map((item) => (
            <div key={item.name} className="flex items-center justify-between gap-4 py-4 text-slate-300"><span>{item.name}</span><strong className="whitespace-nowrap text-white">{formatPrice(item.price)}</strong></div>
          ))}
          <div className="flex items-center justify-between py-4 font-semibold text-emerald-300"><span>Subtotal:</span><strong>{formatPrice(activeOrder.total_amount)}</strong></div>
        </div>
      </div>

      <dl className="relative mt-6 grid gap-3 rounded-xl border border-slate-700 bg-slate-900/60 p-4 text-sm sm:grid-cols-2">
        <div><dt className="text-slate-500">Order ID</dt><dd className="mt-1 break-all text-slate-200">{activeOrder.order_id}</dd></div>
        <div><dt className="text-slate-500">Confirmation #</dt><dd className="mt-1 text-slate-200">Conf_Sep04_9921</dd></div>
        <div><dt className="text-slate-500">Payment Method</dt><dd className="mt-1 text-slate-200">Razorpay</dd></div>
        <div><dt className="text-slate-500">Payment ID</dt><dd className="mt-1 break-all text-slate-200">{paymentId}</dd></div>
        <div className="sm:col-span-2"><dt className="text-slate-500">Estimated Delivery</dt><dd className="mt-1 text-slate-200">Sep 6, 2026.</dd></div>
      </dl>

      <div className="relative mt-4 text-center"><a className="text-xs font-semibold text-cyan-300 underline decoration-cyan-300/40 underline-offset-4 hover:text-cyan-200" onClick={() => alert('Feature arriving in V2 roadmap!')}>Download Tax Invoice</a></div>

      <div className="relative mt-8 flex flex-col justify-center gap-3 sm:flex-row">
        <button type="button" onClick={onStartNewNegotiation} className="rounded-xl bg-emerald-400 px-5 py-3 text-sm font-bold text-[#102238] transition hover:bg-emerald-300">Start New Negotiation</button>
        <button type="button" onClick={() => alert('Feature arriving in V2 roadmap!')} className="rounded-xl border border-slate-600 bg-slate-700 px-5 py-3 text-sm font-semibold text-slate-100 transition hover:bg-slate-600">View Order History</button>
      </div>
    </div>
  )
}