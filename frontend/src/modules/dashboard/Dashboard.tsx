import { useQuery } from "@tanstack/react-query";
import { fetchDashboardOverview } from "@/lib/api/endpoints";
import StatCard from "@/components/ui/StatCard";

export default function Dashboard() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["dashboard-overview"],
    queryFn: fetchDashboardOverview,
  });

  if (isLoading) return <p className="text-gray-500">Yükleniyor...</p>;
  if (error) return <p className="text-red-600">Veri alınamadı. Backend çalışıyor mu?</p>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Genel bakış</h1>
        <p className="text-sm text-gray-500">Şirketin anlık durumu ve AI içgörüleri</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Toplam ürün" value={data?.total_products ?? 0} />
        <StatCard
          label="Düşük stoklu ürün"
          value={data?.low_stock_products ?? 0}
          tone="warning"
        />
        <StatCard label="Toplam müşteri" value={data?.total_customers ?? 0} />
        <StatCard
          label="Anomali işaretli satış"
          value={data?.flagged_anomalous_sales ?? 0}
          tone="danger"
        />
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <h2 className="text-sm font-semibold text-gray-700 mb-2">Sonraki adımlar</h2>
        <ul className="text-sm text-gray-600 space-y-1 list-disc list-inside">
          <li>Talep tahmini grafiklerini buraya ekle (recharts ile)</li>
          <li>En riskli ürünler / müşteriler tablosu ekle</li>
          <li>AI Copilot panelini ana sayfaya küçük widget olarak yerleştir</li>
        </ul>
      </div>
    </div>
  );
}
