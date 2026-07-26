interface StatCardProps {
  label: string;
  value: string | number;
  tone?: "default" | "danger" | "warning";
}

const toneStyles: Record<string, string> = {
  default: "text-gray-900",
  danger: "text-red-600",
  warning: "text-amber-600",
};

export default function StatCard({ label, value, tone = "default" }: StatCardProps) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <p className="text-sm text-gray-500">{label}</p>
      <p className={`text-2xl font-semibold mt-1 ${toneStyles[tone]}`}>{value}</p>
    </div>
  );
}
