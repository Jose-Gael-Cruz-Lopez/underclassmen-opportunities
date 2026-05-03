import { Opportunity } from "@/lib/types";

const STATUS_STYLES: Record<Opportunity["status"], string> = {
  CLOSING_SOON:
    "bg-orange-500/15 text-orange-700 dark:text-orange-300 ring-1 ring-orange-500/30",
  OPEN:
    "bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 ring-1 ring-emerald-500/30",
  OPENS_SOON:
    "bg-blue-500/15 text-blue-700 dark:text-blue-300 ring-1 ring-blue-500/30",
  CLOSED:
    "bg-zinc-500/15 text-zinc-600 dark:text-zinc-400 ring-1 ring-zinc-500/30",
};

const STATUS_TEXT: Record<Opportunity["status"], string> = {
  CLOSING_SOON: "🔥 Closing soon",
  OPEN: "✅ Open",
  OPENS_SOON: "⏳ Opens soon",
  CLOSED: "🔒 Closed",
};

export function OpportunityCard({ opp }: { opp: Opportunity }) {
  const deadlineLabel =
    opp.daysUntilDeadline !== null
      ? opp.daysUntilDeadline === 0
        ? "Today"
        : opp.daysUntilDeadline === 1
        ? "Tomorrow"
        : `${opp.daysUntilDeadline} days`
      : opp.deadlineRaw || "—";

  return (
    <a
      href={opp.url || "#"}
      target="_blank"
      rel="noopener noreferrer"
      className="group flex flex-col gap-3 rounded-xl border border-zinc-200 bg-white p-4 transition-all hover:-translate-y-0.5 hover:border-zinc-300 hover:shadow-md dark:border-zinc-800 dark:bg-zinc-950 dark:hover:border-zinc-700"
    >
      <div className="flex items-center justify-between gap-2">
        <span
          className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
            STATUS_STYLES[opp.status]
          }`}
        >
          {STATUS_TEXT[opp.status]}
        </span>
        <span className="text-xs text-zinc-500 dark:text-zinc-500">
          {opp.sectionLabel}
        </span>
      </div>

      <div>
        <div className="text-xs font-medium uppercase tracking-wide text-zinc-500 dark:text-zinc-500">
          {opp.organization}
        </div>
        <div className="mt-1 text-base font-semibold leading-snug text-zinc-900 group-hover:text-zinc-950 dark:text-zinc-50">
          {opp.title}
        </div>
      </div>

      {opp.type && (
        <div className="line-clamp-2 text-xs text-zinc-600 dark:text-zinc-400">
          {opp.type}
        </div>
      )}

      <div className="mt-auto flex items-center justify-between gap-2 pt-2 text-xs">
        <div className="flex items-center gap-1 text-zinc-600 dark:text-zinc-400">
          <span aria-hidden>📍</span>
          <span className="truncate">{opp.location || "Remote / TBD"}</span>
        </div>
        <div className="flex items-center gap-1 font-medium text-zinc-900 dark:text-zinc-100">
          <span aria-hidden>🗓️</span>
          <span>{deadlineLabel}</span>
        </div>
      </div>
    </a>
  );
}
