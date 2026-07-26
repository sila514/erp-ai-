import type { TooltipProps } from "recharts";

/** Koyu temalı, tüm grafiklerde ortak kullanılan hover tooltip (bkz. dataviz skill - hover layer). */
export default function ChartTooltip({ active, payload, label }: TooltipProps<number, string>) {
  if (!active || !payload?.length) return null;

  return (
    <div className="rounded-lg border border-sky-400/30 bg-navy-950/95 px-3 py-2 text-[11px] shadow-glow-sm backdrop-blur">
      {label !== undefined && <div className="mb-1 font-medium text-sky-100/80">{label}</div>}
      <div className="space-y-0.5">
        {payload.map((entry) => (
          <div key={entry.dataKey as string} className="flex items-center gap-2">
            <span
              className="h-2 w-2 flex-shrink-0 rounded-full"
              style={{ background: entry.color, boxShadow: `0 0 6px ${entry.color}` }}
            />
            <span className="text-sky-300/60">{entry.name}:</span>
            <span className="font-medium text-sky-100/90">
              {typeof entry.value === "number" ? entry.value.toLocaleString("tr-TR") : entry.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
