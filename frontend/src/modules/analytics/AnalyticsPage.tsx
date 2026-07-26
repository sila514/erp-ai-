import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AlertTriangle } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import ChartCard from "@/components/ui/ChartCard";
import ChartTooltip from "@/components/charts/ChartTooltip";
import StatusBadge from "@/components/ui/StatusBadge";
import { correlationColor, correlationTextColor } from "@/lib/divergingColor";
import { SERIES, CHART_GRID, CHART_TICK } from "@/lib/chartColors";
import {
  fetchAcf,
  fetchCorrelationMatrix,
  fetchFeatureImportance,
  fetchProducts,
  type AnalyticsEntity,
} from "@/lib/api/endpoints";

function CausalityDisclaimer() {
  return (
    <div className="flex items-center gap-2.5 rounded-xl border border-amber-400/20 bg-amber-400/[0.06] px-4 py-2.5 text-[12px] text-amber-200/80">
      <AlertTriangle size={14} className="flex-shrink-0 text-amber-300" />
      <span>
        <strong className="font-semibold text-amber-100">Korelasyon nedensellik değildir.</strong> Bu
        sayfadaki tüm sonuçlar yalnızca istatistiksel ilişkiyi gösterir; bir değişkenin diğerini
        "sebep olduğu" anlamına gelmez.
      </span>
    </div>
  );
}

const ENTITY_OPTIONS: { value: AnalyticsEntity; label: string }[] = [
  { value: "sales", label: "Satışlar" },
  { value: "customers", label: "Müşteriler" },
  { value: "products", label: "Ürünler" },
];

function CorrelationSection() {
  const [entity, setEntity] = useState<AnalyticsEntity>("customers");
  const [method, setMethod] = useState<"pearson" | "spearman">("pearson");
  const { data, isLoading, error } = useQuery({
    queryKey: ["correlation-matrix", entity],
    queryFn: () => fetchCorrelationMatrix(entity),
  });

  const rMatrix = data ? (method === "pearson" ? data.pearson_r : data.spearman_r) : null;
  const pMatrix = data ? (method === "pearson" ? data.pearson_p_corrected : data.spearman_p_corrected) : null;

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-[15px] font-bold text-white">Korelasyon Matrisi</div>
          <p className="mt-0.5 text-[11px] text-slate-500">
            Pearson (lineer ilişki) + Spearman (monotonik, lineer olmayan ilişkileri de yakalar) —
            ikisi birlikte hesaplanır.
          </p>
        </div>
        <div className="flex gap-2">
          <div className="flex rounded-lg border border-white/[0.08] bg-white/[0.03] p-0.5">
            {ENTITY_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setEntity(opt.value)}
                className={`rounded-md px-2.5 py-1 text-[11px] font-medium transition-colors ${
                  entity === opt.value ? "bg-sky-500/20 text-sky-200" : "text-slate-500 hover:text-slate-300"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
          <div className="flex rounded-lg border border-white/[0.08] bg-white/[0.03] p-0.5">
            {(["pearson", "spearman"] as const).map((m) => (
              <button
                key={m}
                onClick={() => setMethod(m)}
                className={`rounded-md px-2.5 py-1 text-[11px] font-medium capitalize transition-colors ${
                  method === m ? "bg-fuchsia-500/20 text-fuchsia-200" : "text-slate-500 hover:text-slate-300"
                }`}
              >
                {m}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="glass p-4">
        <div className="glass-glow -right-16 -top-16 h-56 w-56 bg-sky-500/[0.1]" />
        <div className="relative z-10">
          {isLoading && <p className="text-xs text-slate-500">Yükleniyor...</p>}
          {error && <p className="text-xs text-rose-400">Korelasyon matrisi alınamadı.</p>}
          {data && rMatrix && pMatrix && (
            <>
              <div className="overflow-x-auto">
                <table className="border-collapse">
                  <thead>
                    <tr>
                      <th className="w-32" />
                      {data.columns.map((col) => (
                        <th
                          key={col}
                          className="max-w-[70px] px-1 pb-2 text-[9.5px] font-medium text-slate-500"
                          style={{ writingMode: "vertical-rl" }}
                        >
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {data.columns.map((rowLabel, i) => (
                      <tr key={rowLabel}>
                        <td className="whitespace-nowrap pr-2 text-[10.5px] text-slate-400">{rowLabel}</td>
                        {data.columns.map((_, j) => {
                          const r = rMatrix[i][j];
                          const p = pMatrix[i][j];
                          return (
                            <td
                              key={j}
                              title={
                                r === null
                                  ? "Hesaplanamadı"
                                  : `r=${r.toFixed(2)}, düzeltilmiş p=${p !== null ? p.toFixed(3) : "-"}`
                              }
                              className="h-8 w-8 border border-navy-950/60 text-center text-[9.5px] font-medium"
                              style={{
                                background: correlationColor(r),
                                color: correlationTextColor(r),
                              }}
                            >
                              {r !== null ? r.toFixed(1) : "-"}
                              {p !== null && p < 0.05 && i !== j ? "*" : ""}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="mt-3 text-[11px] leading-relaxed text-slate-500">
                Renk yoğunluğu korelasyon katsayısının mutlak değerini gösterir (mavi: pozitif, kırmızı:
                negatif). <span className="text-slate-300">*</span> işareti, çoklu test düzeltmesi
                ({data.correction_method === "fdr_bh" ? "FDR/Benjamini-Hochberg" : data.correction_method})
                sonrası hâlâ istatistiksel olarak anlamlı (düzeltilmiş p&lt;0.05) olan ilişkileri
                işaretler — {data.n_pairs_tested} çift test edildiğinden düzeltme yapılmadan bazı
                ilişkiler şans eseri anlamlı görünebilirdi. n={data.n_observations} gözlem.
              </p>

              <div className="mt-5">
                <div className="mb-2 text-[12px] font-semibold text-slate-300">
                  VIF (Multicollinearity) — eşik: {data.vif.vif_threshold}
                </div>
                <table className="w-full text-left text-[11.5px]">
                  <thead>
                    <tr className="text-[10px] uppercase tracking-wide text-sky-400/35">
                      <th className="pb-1.5">Feature</th>
                      <th className="pb-1.5">VIF</th>
                      <th className="pb-1.5">Durum</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-sky-400/[0.06]">
                    {data.vif.results.map((row) => (
                      <tr key={row.feature}>
                        <td className="py-1.5 text-slate-300">{row.feature}</td>
                        <td className="py-1.5 font-mono text-slate-400">
                          {row.vif !== null ? row.vif.toFixed(1) : "-"}
                        </td>
                        <td className="py-1.5">
                          {row.high_multicollinearity ? (
                            <StatusBadge tone="critical" label="Yüksek VIF" />
                          ) : (
                            <StatusBadge tone="good" label="Normal" />
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {data.vif.recommendation && (
                  <p className="mt-2 text-[11px] leading-relaxed text-slate-500">{data.vif.recommendation}</p>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function AcfSection() {
  const { data: products } = useQuery({ queryKey: ["products"], queryFn: fetchProducts });
  const [productId, setProductId] = useState<string>("");
  const activeId = productId || products?.[0]?.id || "";

  const { data, isLoading, error } = useQuery({
    queryKey: ["acf", activeId],
    queryFn: () => fetchAcf(activeId, 30),
    enabled: !!activeId,
  });

  const chartData = useMemo(
    () => (data ? data.lags.map((lag, i) => ({ lag, acf: data.acf[i], pacf: data.pacf[i] })) : []),
    [data]
  );

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-[15px] font-bold text-white">Zaman Serisi Analizi — ACF / PACF</div>
          <p className="mt-0.5 text-[11px] text-slate-500">
            Otokorelasyon (ACF) ve kısmi otokorelasyon (PACF) — lag feature seçimini gerekçelendirir.
          </p>
        </div>
        <select
          value={activeId}
          onChange={(e) => setProductId(e.target.value)}
          className="rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-1.5 text-[11px] text-slate-300 focus:outline-none"
        >
          {products?.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
      </div>

      {isLoading && <p className="text-xs text-slate-500">Yükleniyor...</p>}
      {error && <p className="text-xs text-rose-400">ACF/PACF hesaplanamadı (yetersiz geçmiş veri olabilir).</p>}

      {data && (
        <>
          <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
            <ChartCard title="ACF" subtitle="Otokorelasyon fonksiyonu">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData}>
                  <CartesianGrid stroke={CHART_GRID} vertical={false} />
                  <XAxis dataKey="lag" tick={{ fontSize: 10, fill: CHART_TICK }} />
                  <YAxis tick={{ fontSize: 10, fill: CHART_TICK }} domain={[-1, 1]} />
                  <Tooltip content={<ChartTooltip />} />
                  <Bar dataKey="acf" name="ACF" fill={SERIES.blue} radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>
            <ChartCard title="PACF" subtitle="Kısmi otokorelasyon fonksiyonu">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData}>
                  <CartesianGrid stroke={CHART_GRID} vertical={false} />
                  <XAxis dataKey="lag" tick={{ fontSize: 10, fill: CHART_TICK }} />
                  <YAxis tick={{ fontSize: 10, fill: CHART_TICK }} domain={[-1, 1]} />
                  <Tooltip content={<ChartTooltip />} />
                  <Bar dataKey="pacf" name="PACF" fill={SERIES.magenta} radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>
          <div className="glass p-4">
            <div className="glass-glow -right-16 -top-16 h-48 w-48 bg-indigo-500/[0.1]" />
            <div className="relative z-10 grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <div className="text-[10px] text-sky-400/40">ADF Stationarity Testi (ham seri)</div>
                <div className="text-[12px] text-slate-300">
                  p={data.adf_test.p_value.toFixed(4)} —{" "}
                  {data.adf_test.is_stationary ? (
                    <span className="text-emerald-300">durağan</span>
                  ) : (
                    <span className="text-amber-300">durağan değil (trend var)</span>
                  )}
                </div>
              </div>
              <div>
                <div className="text-[10px] text-sky-400/40">ADF Testi (differencing sonrası)</div>
                <div className="text-[12px] text-slate-300">
                  p={data.differenced_adf_test.p_value.toFixed(4)} —{" "}
                  {data.differenced_adf_test.is_stationary ? (
                    <span className="text-emerald-300">durağan</span>
                  ) : (
                    <span className="text-amber-300">durağan değil</span>
                  )}
                </div>
              </div>
            </div>
            <p className="relative z-10 mt-3 text-[11px] leading-relaxed text-slate-500">
              Seri durağan değilse (trend içeriyorsa), ham korelasyon "spurious" (sahte) olabilir —
              differencing (ardışık farkları alma) trendi temizleyip gerçek ilişkiyi ortaya çıkarır.
              ACF'te lag=7'de görülen belirgin bir sıçrama, haftalık mevsimselliğin `lag_7` feature'ı
              olarak modele eklenmesini gerekçelendirir.
            </p>
          </div>
        </>
      )}
    </div>
  );
}

const TARGET_OPTIONS = [
  { value: "churn" as const, label: "Churn" },
  { value: "demand" as const, label: "Talep Tahmini" },
];

function FeatureImportanceSection() {
  const [target, setTarget] = useState<"churn" | "demand">("churn");
  const { data: products } = useQuery({ queryKey: ["products"], queryFn: fetchProducts });
  const [productId, setProductId] = useState<string>("");
  const activeProductId = productId || products?.[0]?.id;

  const { data, isLoading, error } = useQuery({
    queryKey: ["feature-importance", target, target === "demand" ? activeProductId : null],
    queryFn: () => fetchFeatureImportance(target, target === "demand" ? activeProductId : undefined),
    enabled: target === "churn" || !!activeProductId,
  });

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-[15px] font-bold text-white">Feature — Hedef Önem Sıralaması</div>
          <p className="mt-0.5 text-[11px] text-slate-500">
            Korelasyon (lineer) + mutual information (lineer olmayan bağımlılıklar dahil) birlikte.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex rounded-lg border border-white/[0.08] bg-white/[0.03] p-0.5">
            {TARGET_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setTarget(opt.value)}
                className={`rounded-md px-2.5 py-1 text-[11px] font-medium transition-colors ${
                  target === opt.value ? "bg-sky-500/20 text-sky-200" : "text-slate-500 hover:text-slate-300"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
          {target === "demand" && (
            <select
              value={activeProductId ?? ""}
              onChange={(e) => setProductId(e.target.value)}
              className="rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-1.5 text-[11px] text-slate-300 focus:outline-none"
            >
              {products?.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          )}
        </div>
      </div>

      <div className="glass p-4">
        <div className="glass-glow -right-16 -top-16 h-48 w-48 bg-fuchsia-500/[0.1]" />
        <div className="relative z-10">
          {isLoading && <p className="text-xs text-slate-500">Yükleniyor...</p>}
          {error && <p className="text-xs text-rose-400">Hesaplanamadı (yetersiz veri olabilir).</p>}
          {data && (
            <>
              <ResponsiveContainer width="100%" height={Math.max(160, data.results.length * 34)}>
                <BarChart data={data.results} layout="vertical" margin={{ left: 24 }}>
                  <CartesianGrid stroke={CHART_GRID} horizontal={false} />
                  <XAxis type="number" tick={{ fontSize: 10, fill: CHART_TICK }} />
                  <YAxis
                    type="category"
                    dataKey="feature"
                    tick={{ fontSize: 10.5, fill: CHART_TICK }}
                    width={140}
                  />
                  <Tooltip content={<ChartTooltip />} />
                  <Bar dataKey="mutual_information" name="Mutual Information" fill={SERIES.aqua} radius={[0, 3, 3, 0]} />
                </BarChart>
              </ResponsiveContainer>

              <table className="mt-4 w-full text-left text-[11.5px]">
                <thead>
                  <tr className="text-[10px] uppercase tracking-wide text-sky-400/35">
                    <th className="pb-1.5">Feature</th>
                    <th className="pb-1.5">Korelasyon</th>
                    <th className="pb-1.5">Düzeltilmiş p</th>
                    <th className="pb-1.5">Anlamlı mı</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-sky-400/[0.06]">
                  {data.results.map((row) => (
                    <tr key={row.feature}>
                      <td className="py-1.5 text-slate-300">{row.feature}</td>
                      <td className="py-1.5 font-mono text-slate-400">
                        {row.correlation !== null ? row.correlation.toFixed(3) : "-"}
                      </td>
                      <td className="py-1.5 font-mono text-slate-400">
                        {row.p_value_corrected !== null ? row.p_value_corrected.toFixed(4) : "-"}
                      </td>
                      <td className="py-1.5">
                        {row.significant ? (
                          <StatusBadge tone="good" label="Anlamlı" />
                        ) : (
                          <StatusBadge tone="warning" label="Anlamlı değil" />
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="mt-3 text-[11px] leading-relaxed text-slate-500">
                "Anlamlı" etiketi, {data.correction_method === "fdr_bh" ? "FDR" : data.correction_method}
                {" "}düzeltmesi sonrası düzeltilmiş p-value&lt;0.05 olan feature'ları gösterir — çoklu
                test düzeltmesi olmadan bu sayıda feature test edildiğinde bazıları şans eseri anlamlı
                çıkabilirdi.
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default function AnalyticsPage() {
  return (
    <div className="space-y-6">
      <CausalityDisclaimer />
      <CorrelationSection />
      <AcfSection />
      <FeatureImportanceSection />
    </div>
  );
}
