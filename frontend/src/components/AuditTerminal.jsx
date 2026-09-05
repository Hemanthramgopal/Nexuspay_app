const statusStyles = {
  pending: 'border border-slate-700/70 bg-slate-800/50 text-slate-300',
  success: 'border border-emerald-900/50 bg-emerald-900/20 text-emerald-400',
  blocked: 'border border-rose-900/50 bg-rose-900/20 text-rose-400',
}

export function AuditTerminal({ entries }) {
  return (
    <aside className="rounded-2xl border border-slate-800 bg-[#0a1128] p-4 shadow-xl shadow-slate-300/30">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-xs font-semibold uppercase tracking-[0.26em] text-slate-400">Audit Terminal</h2>
        <span className="rounded-full border border-slate-700 bg-slate-800 px-2 py-1 text-[10px] uppercase tracking-[0.25em] text-slate-300">
          Trace
        </span>
      </div>

      <div className="space-y-3 font-mono text-sm">
        {entries.map((entry, index) => {
          const isFailure = entry.status === 'blocked'
          const isOrderCreated = entry.step === 'ORDER_CREATED'
          const isUpsellPitch = entry.step === 'UPSELL_PITCH_GENERATED'
          const isComboGuardrail = entry.step === 'COMBO_GUARDRAIL_PASSED'
          const isOrderUpdated = entry.step === 'ORDER_UPDATED'
          const isMandateGenerated = entry.step === 'MANDATE_GENERATED'
          const isLlmBenchmark = entry.step === 'LLM_ROUTER_BENCHMARK'

          return (
            <div
              key={entry.traceId ?? `${entry.step}-${index}`}
              className={`rounded-xl p-3 ${statusStyles[entry.status] ?? statusStyles.pending} ${
                isOrderCreated ? 'shadow-[0_0_18px_rgba(52,211,153,0.16)]' : ''
              } ${
                isUpsellPitch ? 'border border-amber-700/50 bg-amber-900/20 text-amber-300' : ''
              } ${
                isComboGuardrail ? 'border border-blue-700/50 bg-blue-900/20 text-blue-300' : ''
              } ${
                isOrderUpdated ? 'border border-emerald-700/50 bg-emerald-900/20 text-emerald-300' : ''
              } ${
                isMandateGenerated ? 'border border-cyan-700/50 bg-cyan-900/20 text-cyan-300' : ''
              } ${
                isLlmBenchmark ? 'border border-violet-700/50 bg-violet-900/20 text-violet-300' : ''
              } ${
                isFailure ? 'shadow-[0_0_0_1px_rgba(251,113,133,0.18)]' : ''
              }`}
            >
              <div className="mb-1 flex items-center justify-between gap-2">
                <span className="text-[10px] font-semibold uppercase tracking-[0.24em] text-slate-300">
                  {entry.step}
                </span>
                <span
                  className={`rounded-full px-2 py-0.5 text-[9px] font-bold uppercase tracking-[0.2em] ${
                    entry.status === 'success'
                      ? isUpsellPitch
                        ? 'bg-amber-500/10 text-amber-300'
                        : isComboGuardrail
                          ? 'bg-blue-500/10 text-blue-300'
                          : isOrderUpdated
                            ? 'bg-emerald-500/10 text-emerald-400'
                            : isMandateGenerated
                              ? 'bg-cyan-500/10 text-cyan-300'
                              : isLlmBenchmark
                                ? 'bg-violet-500/10 text-violet-300'
                              : 'bg-emerald-500/10 text-emerald-400'
                      : entry.status === 'blocked'
                        ? 'bg-rose-500/10 text-rose-400'
                        : 'bg-slate-700 text-slate-300'
                  }`}
                >
                  {entry.status}
                </span>
              </div>
              <p
                className={
                  isFailure
                    ? 'text-rose-400'
                    : isUpsellPitch
                      ? 'text-amber-300'
                      : isComboGuardrail
                        ? 'text-blue-300'
                        : isOrderUpdated
                          ? 'text-emerald-300'
                          : isMandateGenerated
                            ? 'text-cyan-300'
                            : isLlmBenchmark
                              ? 'text-violet-300'
                            : 'text-emerald-400'
                }
              >
                {entry.detail}
              </p>
            </div>
          )
        })}
      </div>
    </aside>
  )
}
