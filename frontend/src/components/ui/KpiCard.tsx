import { useEffect, useRef, useState } from "react";
import type { LucideIcon } from "lucide-react";
import { TrendingDown, TrendingUp } from "lucide-react";

interface KpiCardProps {
  label: string;
  value: string | number;
  icon: LucideIcon;
  accent?: "blue" | "magenta";
  trend?: { direction: "up" | "down"; label: string; tone?: "good" | "critical" };
  /** 0-100 arası; verilmezse ilerleme çubuğu gösterilmez */
  progress?: number;
}

const accentStyles = {
  blue: {
    bg: "from-navy-800 via-[#0d2870] to-navy-800",
    glow: "bg-glow-blue",
    icoBg: "bg-sky-400/15 shadow-[0_0_12px_rgba(0,180,255,0.2)]",
    icoColor: "text-sky-400",
    value: "text-sky-300 [text-shadow:0_0_20px_rgba(0,180,255,0.35)]",
    bar: "from-sky-600 to-sky-400",
  },
  magenta: {
    bg: "from-[#1a0a3a] via-[#3a1450] to-[#1a0a3a]",
    glow: "bg-fuchsia-400",
    icoBg: "bg-fuchsia-400/15 shadow-[0_0_12px_rgba(213,81,129,0.25)]",
    icoColor: "text-fuchsia-300",
    value: "text-fuchsia-300 [text-shadow:0_0_20px_rgba(213,81,129,0.35)]",
    bar: "from-fuchsia-600 to-fuchsia-400",
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
  const styles = accentStyles[accent];
  const [barWidth, setBarWidth] = useState(0);
  const mounted = useRef(false);

  useEffect(() => {
    if (progress === undefined || mounted.current) return;
    mounted.current = true;
    const t = setTimeout(() => setBarWidth(progress), 200);
    return () => clearTimeout(t);
  }, [progress]);

  return (
    <div className="kpi-card">
      <div className={`kpi-card-bg bg-gradient-to-br ${styles.bg}`} />
      <div className={`kpi-card-glow ${styles.glow}`} />
      <div className="relative z-10">
        <div className="mb-2 flex items-center gap-2">
          <div className={`flex h-7 w-7 items-center justify-center rounded-md ${styles.icoBg}`}>
            <Icon size={14} className={styles.icoColor} />
          </div>
          <span className="text-[11px] tracking-wide text-sky-200/50">{label}</span>
        </div>
        <div className={`mb-1 text-2xl font-bold leading-none ${styles.value}`}>{value}</div>

        {progress !== undefined && (
          <>
            <div className="my-1.5 h-px bg-gradient-to-r from-transparent via-sky-400/25 to-transparent" />
            <div className="h-[3px] overflow-hidden rounded-full bg-sky-400/10">
              <div
                className={`h-full rounded-full bg-gradient-to-r ${styles.bar} transition-[width] duration-1000 ease-out`}
                style={{ width: `${barWidth}%` }}
              />
            </div>
          </>
        )}

        {trend && (
          <div
            className={`mt-1 flex items-center gap-1 text-[11px] ${
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
