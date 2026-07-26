/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Koyu zemin skalası (near-black, mavi alt ton)
        navy: {
          950: "#05060f",
          900: "#0a0e1f",
          800: "#111530",
          700: "#181d42",
        },
        // Arka plan "aurora" mesh'i ve UI gradyanları için - tek renkli/dekoratif
        // kullanım (arkaplan blob'ları, buton/ikon gradyanları, başlık vurgusu).
        // Birden fazla seri aynı grafikte yan yana geldiğinde bunun yerine `series.*`
        // kullanılır (CVD/erişilebilirlik doğrulaması yalnızca o set için yapıldı -
        // bkz. dataviz skill / scripts/validate_palette.js).
        aurora: {
          indigo: "#6366f1",
          violet: "#8b5cf6",
          fuchsia: "#d946ef",
          sky: "#38bdf8",
          cyan: "#22d3ee",
          rose: "#fb7185",
          amber: "#fbbf24",
          emerald: "#34d399",
        },
        glow: {
          blue: "#38bdf8",
        },
        // Kategorik grafik serileri - SABİT sırayla kullanılmalı, karıştırılmamalı.
        // node scripts/validate_palette.js "#3987e5,#d95926,#199e70,#c98500,#d55181" --mode dark --surface "#040c1e"
        // => tüm kontroller (lightness/chroma/CVD/normal-vision/contrast) geçti (adjacent-pairs).
        series: {
          1: "#3987e5", // mavi
          2: "#d95926", // turuncu
          3: "#199e70", // aqua/yeşil
          4: "#c98500", // amber
          5: "#d55181", // magenta
        },
        // Durum rengi paleti - kategorik seri renklerinden kasıtlı olarak farklı
        // (bir durum rengi asla bir seriyle karıştırılmamalı). Her zaman ikon/etiketle
        // birlikte kullanılır, tek başına renkle anlam taşımaz.
        status: {
          good: "#0ca30c",
          warning: "#fab219",
          serious: "#ec835a",
          critical: "#d03b3b",
        },
        // Diverging (kutupsal) ölçek - SADECE korelasyon/fark gibi işaretli
        // (pozitif/negatif) büyüklükler için (örn. korelasyon heatmap). `series.1`
        // (mavi) ile aynı hue kasıtlı; kırmızı, dataviz skill'inin referans
        // paletindeki aynı 8'li kategorik sıranın doğrulanmış koyu-mod kırmızı
        // adımından (slot 8) alındı. Bu sandbox'ta node/validate_palette.js
        // çalıştırılamadığı için bu ikili ayrıca koşulmadı - yeni bir uçtan uca
        // görsel değişiklik öncesi doğrulanmalı.
        diverging: {
          positive: "#3987e5",
          negative: "#e66767",
          neutral: "#334155",
        },
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "sans-serif"],
      },
      boxShadow: {
        "glow-sm": "0 0 16px rgba(56,189,248,.3)",
        "glow-md": "0 0 24px rgba(56,189,248,.35), 0 0 48px rgba(99,102,241,.18)",
        "glow-violet": "0 0 20px rgba(139,92,246,.35)",
        "glow-fuchsia": "0 0 20px rgba(217,70,239,.3)",
        glass: "0 1px 0 0 rgba(255,255,255,.06) inset, 0 8px 32px -8px rgba(0,0,0,.55)",
        lift: "0 1px 0 0 rgba(255,255,255,.08) inset, 0 24px 48px -12px rgba(0,0,0,.6), 0 0 32px -4px rgba(99,102,241,.25)",
      },
      keyframes: {
        drift: {
          "0%, 100%": { transform: "translate(0, 0) scale(1)" },
          "33%": { transform: "translate(3%, -4%) scale(1.06)" },
          "66%": { transform: "translate(-2%, 3%) scale(0.98)" },
        },
        "drift-slow": {
          "0%, 100%": { transform: "translate(0, 0) scale(1)" },
          "50%": { transform: "translate(-4%, 4%) scale(1.08)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "0% 50%" },
          "100%": { backgroundPosition: "200% 50%" },
        },
      },
      animation: {
        drift: "drift 22s ease-in-out infinite",
        "drift-slow": "drift-slow 30s ease-in-out infinite",
        shimmer: "shimmer 3s linear infinite",
      },
    },
  },
  plugins: [],
};
