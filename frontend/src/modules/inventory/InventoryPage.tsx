import { useQuery } from "@tanstack/react-query";
import { fetchProducts } from "@/lib/api/endpoints";

const riskBadgeStyle: Record<string, string> = {
  high: "bg-red-100 text-red-700",
  medium: "bg-amber-100 text-amber-700",
  low: "bg-green-100 text-green-700",
};

export default function InventoryPage() {
  const { data: products, isLoading } = useQuery({
    queryKey: ["products"],
    queryFn: fetchProducts,
  });

  if (isLoading) return <p className="text-gray-500">Yükleniyor...</p>;

  return (
    <div>
      <h1 className="text-xl font-semibold text-gray-900 mb-4">Stok yönetimi</h1>

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-500 text-left">
            <tr>
              <th className="px-4 py-2">SKU</th>
              <th className="px-4 py-2">Ürün</th>
              <th className="px-4 py-2">Kategori</th>
              <th className="px-4 py-2">Stok</th>
              <th className="px-4 py-2">Yeniden sipariş eşiği</th>
              <th className="px-4 py-2">Durum</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {products?.map((p) => {
              const isLow = p.stock_quantity <= p.reorder_level;
              return (
                <tr key={p.id}>
                  <td className="px-4 py-2 font-mono text-xs text-gray-500">{p.sku}</td>
                  <td className="px-4 py-2">{p.name}</td>
                  <td className="px-4 py-2 text-gray-500">{p.category ?? "-"}</td>
                  <td className="px-4 py-2">{p.stock_quantity}</td>
                  <td className="px-4 py-2 text-gray-500">{p.reorder_level}</td>
                  <td className="px-4 py-2">
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full ${
                        isLow ? riskBadgeStyle.high : riskBadgeStyle.low
                      }`}
                    >
                      {isLow ? "Düşük stok" : "Normal"}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-gray-400 mt-2">
        Not: "Düşük stok" etiketi basit eşik kontrolüdür. Detaylı risk skoru için
        ürün detay sayfasında ML servisinden gelen /stock-risk sonucu gösterilmeli.
      </p>
    </div>
  );
}
