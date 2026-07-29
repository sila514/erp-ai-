import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { LogIn, Sparkles } from "lucide-react";
import AuroraBackground from "@/components/ui/AuroraBackground";
import { useAuthStore } from "@/stores/authStore";

export default function LoginPage() {
  const login = useAuthStore((s) => s.login);
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from ?? "/";

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!username || !password) return;
    setError(null);
    setLoading(true);
    try {
      await login(username, password);
      navigate(from, { replace: true });
    } catch {
      setError("Kullanıcı adı veya şifre hatalı");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="relative flex h-screen items-center justify-center text-slate-200">
      <AuroraBackground />

      <form onSubmit={handleSubmit} className="glass relative z-10 w-full max-w-sm p-6">
        <div className="glass-glow -right-16 -top-16 h-56 w-56 bg-indigo-500/20" />
        <div className="glass-glow -left-16 bottom-0 top-auto h-48 w-48 bg-fuchsia-500/15" />

        <div className="relative z-10 mb-6 flex flex-col items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-sky-400 via-indigo-500 to-fuchsia-500 text-base font-extrabold text-white shadow-glow-md">
            E
          </div>
          <div className="text-center">
            <div className="text-[15px] font-bold text-white">
              <span className="text-gradient">ERP AI</span>
            </div>
            <div className="text-[11px] text-slate-500">Yönetim paneline giriş yap</div>
          </div>
        </div>

        <div className="relative z-10 space-y-3">
          <div>
            <label className="mb-1 block text-[11px] font-medium text-slate-400">
              Kullanıcı adı
            </label>
            <input
              autoFocus
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="admin"
              className="w-full rounded-xl border border-white/[0.08] bg-white/[0.04] px-3 py-2.5 text-[13px] text-white placeholder:text-slate-500 backdrop-blur focus:outline-none focus:ring-2 focus:ring-sky-400/40"
            />
          </div>
          <div>
            <label className="mb-1 block text-[11px] font-medium text-slate-400">Şifre</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full rounded-xl border border-white/[0.08] bg-white/[0.04] px-3 py-2.5 text-[13px] text-white placeholder:text-slate-500 backdrop-blur focus:outline-none focus:ring-2 focus:ring-sky-400/40"
            />
          </div>

          {error && <p className="text-[12px] text-status-critical">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-br from-sky-500 via-indigo-500 to-fuchsia-500 px-4 py-2.5 text-[13px] font-medium text-white shadow-glow-md transition-transform hover:scale-[1.02] disabled:opacity-60 disabled:hover:scale-100"
          >
            <LogIn size={15} />
            {loading ? "Giriş yapılıyor..." : "Giriş yap"}
          </button>
        </div>

        <div className="relative z-10 mt-5 flex items-center gap-1.5 text-[10.5px] text-slate-500">
          <Sparkles size={12} className="text-sky-300/70" />
          Demo: admin / admin123 (seed script ile oluşturulur)
        </div>
      </form>
    </div>
  );
}
