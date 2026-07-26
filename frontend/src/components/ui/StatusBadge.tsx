import { AlertTriangle, CheckCircle2, OctagonAlert, TriangleAlert } from "lucide-react";

export type StatusTone = "good" | "warning" | "serious" | "critical";

const config: Record<StatusTone, { className: string; Icon: typeof CheckCircle2 }> = {
  good: { className: "badge-good", Icon: CheckCircle2 },
  warning: { className: "badge-warning", Icon: TriangleAlert },
  serious: { className: "badge-serious", Icon: AlertTriangle },
  critical: { className: "badge-critical", Icon: OctagonAlert },
};

/**
 * Durum rengi ASLA tek başına anlam taşımaz: her zaman ikon + etiket birlikte.
 * (bkz. dataviz skill - status renkleri kategorik seri renklerinden ayrı tutulur)
 */
export default function StatusBadge({ tone, label }: { tone: StatusTone; label: string }) {
  const { className, Icon } = config[tone];
  return (
    <span className={`badge ${className}`}>
      <Icon size={11} />
      {label}
    </span>
  );
}
