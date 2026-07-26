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
    <div className="card-dark">
      <div className="pointer-events-none absolute -right-16 -top-16 h-44 w-44 rounded-full bg-sky-400/[0.06] blur-3xl" />
      <div className="relative z-10 mb-3 flex items-start justify-between gap-2">
        <div>
          <div className="text-[13px] font-semibold text-sky-100/90">{title}</div>
          {subtitle && <div className="mt-0.5 text-[11px] text-sky-400/40">{subtitle}</div>}
        </div>
        {badge}
      </div>
      <div className="relative z-10" style={{ height }}>
        {children}
      </div>
    </div>
  );
}
