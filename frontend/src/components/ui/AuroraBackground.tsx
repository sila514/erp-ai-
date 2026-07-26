/**
 * Sabit, yavaşça süzülen çok renkli gradyan mesh arka planı. DashboardLayout'ta
 * bir kez mount edilir; tüm sayfalarda aynı kalır (route değişince yeniden başlamaz).
 */
export default function AuroraBackground() {
  return (
    <div className="aurora-field">
      {/* Alt kat: köşegen bir taban gradyanı - saf düz siyahlığı kırar */}
      <div
        className="absolute inset-0"
        style={{
          background:
            "linear-gradient(135deg, #0b0f2e 0%, #05060f 35%, #05060f 65%, #180b2e 100%)",
        }}
      />

      <div
        className="aurora-blob animate-drift left-[-12%] top-[-20%] h-[680px] w-[680px] bg-indigo-500/45"
        style={{ animationDelay: "0s" }}
      />
      <div
        className="aurora-blob animate-drift-slow right-[-18%] top-[-15%] h-[620px] w-[620px] bg-fuchsia-500/40"
        style={{ animationDelay: "-6s" }}
      />
      <div
        className="aurora-blob animate-drift left-[25%] top-[30%] h-[520px] w-[520px] bg-sky-400/35"
        style={{ animationDelay: "-12s" }}
      />
      <div
        className="aurora-blob animate-drift-slow bottom-[-25%] right-[5%] h-[700px] w-[700px] bg-violet-600/45"
        style={{ animationDelay: "-18s" }}
      />
      <div
        className="aurora-blob animate-drift bottom-[-15%] left-[5%] h-[460px] w-[460px] bg-emerald-400/25"
        style={{ animationDelay: "-9s" }}
      />
      <div
        className="aurora-blob animate-drift-slow left-[45%] bottom-[10%] h-[400px] w-[400px] bg-rose-400/25"
        style={{ animationDelay: "-3s" }}
      />

      {/* İnce nokta dokusu - saf düz zeminin "flat" hissini kırar */}
      <div
        className="absolute inset-0 opacity-[0.12]"
        style={{
          backgroundImage: "radial-gradient(rgba(255,255,255,0.6) 0.6px, transparent 0.6px)",
          backgroundSize: "26px 26px",
        }}
      />

      {/* Vinyet: kenarlara doğru koyulaşma, merkez ferahlığı korur */}
      <div
        className="absolute inset-0"
        style={{
          background: "radial-gradient(ellipse at center, transparent 40%, rgba(5,6,15,0.7) 100%)",
        }}
      />
    </div>
  );
}
