import type { ReactNode } from "react";

interface ChartCardProps {
  title: string;
  subtitle?: string;
  badge?: ReactNode;
  height?: number;
  children: ReactNode;
}

export default function ChartCard({ title, subtitle, badge, height = 220, children }: ChartCardProps) {
  return (
    <div className="glass glass-hover">
      <div className="glass-glow -right-20 -top-20 h-56 w-56 bg-indigo-500/[0.12]" />
      <div className="relative z-10 mb-3 flex items-start justify-between gap-2">
        <div>
          <div className="text-[13px] font-semibold text-white">{title}</div>
          {subtitle && <div className="mt-0.5 text-[11px] text-slate-500">{subtitle}</div>}
        </div>
        {badge}
      </div>
      <div className="relative z-10" style={{ height }}>
        {children}
      </div>
    </div>
  );
}
