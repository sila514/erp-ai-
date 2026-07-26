/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Koyu lacivert zemin skalası
        navy: {
          950: "#040c1e",
          900: "#071428",
          800: "#0a2560",
          700: "#0d2870",
        },
        // Marka/glow rengi - tek renkli kullanım (logo, KPI parlama, başlık vurgusu).
        // Birden fazla seri aynı grafikte yan yana geldiğinde bunun yerine `series.*`
        // kullanılır (CVD/erişilebilirlik doğrulaması yalnızca o set için yapıldı -
        // bkz. dataviz skill / scripts/validate_palette.js).
        glow: {
          blue: "#00b4ff",
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
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "sans-serif"],
      },
      boxShadow: {
        "glow-sm": "0 0 12px rgba(0,180,255,.25)",
        "glow-md": "0 0 20px rgba(0,180,255,.35), 0 0 40px rgba(0,100,200,.15)",
        "glow-purple": "0 0 12px rgba(213,81,129,.3)",
      },
    },
  },
  plugins: [],
};
