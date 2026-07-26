import { useEffect, useRef, useState } from "react";
import type { CSSProperties } from "react";
import type { LucideIcon } from "lucide-react";
import { TrendingDown, TrendingUp } from "lucide-react";

export type KpiAccent = "blue" | "magenta" | "emerald" | "amber" | "violet";

interface KpiCardProps {
  label: string;
  value: string | number;
  icon: LucideIcon;
  accent?: KpiAccent;
  trend?: { direction: "up" | "down"; label: string; tone?: "good" | "critical" };
  /** 0-100 arası; verilmezse ilerleme çubuğu gösterilmez */
  progress?: number;
}

const accentStyles: Record<
  KpiAccent,
  { a: string; b: string; icoBg: string; icoColor: string; text: string; bar: string; glowA: string; glowB: string }
> = {
  blue: {
    a: "#38bdf8",
    b: "#6366f1",
    icoBg: "bg-gradient-to-br from-sky-400/60 to-indigo-500/50 shadow-[0_0_14px_rgba(56,189,248,0.25)]",
    icoColor: "text-white",
    text: "bg-gradient-to-r from-sky-300 via-sky-400 to-indigo-300",
    bar: "from-sky-500 to-indigo-400",
    glowA: "bg-sky-400/25",
    glowB: "bg-indigo-500/20",
  },
  magenta: {
    a: "#d946ef",
    b: "#fb7185",
    icoBg: "bg-gradient-to-br from-fuchsia-400/60 to-rose-400/50 shadow-[0_0_14px_rgba(217,70,239,0.25)]",
    icoColor: "text-white",
    text: "bg-gradient-to-r from-fuchsia-300 via-fuchsia-400 to-rose-300",
    bar: "from-fuchsia-500 to-rose-400",
    glowA: "bg-fuchsia-400/25",
    glowB: "bg-rose-400/15",
  },
  emerald: {
    a: "#34d399",
    b: "#38bdf8",
    icoBg: "bg-gradient-to-br from-emerald-400/60 to-sky-400/45 shadow-[0_0_14px_rgba(52,211,153,0.25)]",
    icoColor: "text-white",
    text: "bg-gradient-to-r from-emerald-300 via-emerald-400 to-sky-300",
    bar: "from-emerald-500 to-sky-400",
    glowA: "bg-emerald-400/20",
    glowB: "bg-sky-400/15",
  },
  amber: {
    a: "#fbbf24",
    b: "#fb7185",
    icoBg: "bg-gradient-to-br from-amber-400/60 to-rose-400/45 shadow-[0_0_14px_rgba(251,191,36,0.22)]",
    icoColor: "text-white",
    text: "bg-gradient-to-r from-amber-300 via-amber-400 to-rose-300",
    bar: "from-amber-500 to-rose-400",
    glowA: "bg-amber-400/20",
    glowB: "bg-rose-400/10",
  },
  violet: {
    a: "#8b5cf6",
    b: "#d946ef",
    icoBg: "bg-gradient-to-br from-violet-400/60 to-fuchsia-400/50 shadow-[0_0_14px_rgba(139,92,246,0.25)]",
    icoColor: "text-white",
    text: "bg-gradient-to-r from-violet-300 via-violet-400 to-fuchsia-300",
    bar: "from-violet-500 to-fuchsia-400",
    glowA: "bg-violet-400/20",
    glowB: "bg-fuchsia-400/15",
  },
};

export default function KpiCard({
  label,
  value,
  icon: Icon,
  accent = "blue",
  trend,
  progress,
}: KpiCardProps) {
  const s = accentStyles[accent];
  const [barWidth, setBarWidth] = useState(0);
  const mounted = useRef(false);

  useEffect(() => {
    if (progress === undefined || mounted.current) return;
    mounted.current = true;
    const t = setTimeout(() => setBarWidth(progress), 200);
    return () => clearTimeout(t);
  }, [progress]);

  return (
    <div className="kpi-card" style={{ "--kpi-a": s.a, "--kpi-b": s.b } as CSSProperties}>
      <div className={`glass-glow -right-8 -top-8 h-28 w-28 ${s.glowA}`} />
      <div className={`glass-glow -left-10 bottom-0 top-auto h-24 w-24 ${s.glowB}`} />
      <div className="relative z-10">
        <div className="mb-2.5 flex items-center gap-2">
          <div className={`flex h-7 w-7 items-center justify-center rounded-lg ${s.icoBg}`}>
            <Icon size={14} className={s.icoColor} />
          </div>
          <span className="text-[11px] font-medium tracking-wide text-slate-400">{label}</span>
        </div>
        <div className={`mb-1 bg-clip-text text-[26px] font-extrabold leading-none text-transparent ${s.text}`}>
          {value}
        </div>

        {progress !== undefined && (
          <>
            <div className="my-2 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />
            <div className="h-[3px] overflow-hidden rounded-full bg-white/[0.06]">
              <div
                className={`h-full rounded-full bg-gradient-to-r ${s.bar} transition-[width] duration-1000 ease-out`}
                style={{ width: `${barWidth}%` }}
              />
            </div>
          </>
        )}

        {trend && (
          <div
            className={`mt-1.5 flex items-center gap-1 text-[11px] font-medium ${
              trend.tone === "critical" ? "text-rose-400" : "text-emerald-400"
            }`}
          >
            {trend.direction === "up" ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
            {trend.label}
          </div>
        )}
      </div>
    </div>
  );
}
