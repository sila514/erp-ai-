import { useState } from "react";
import { Send, Sparkles } from "lucide-react";
import { askCopilot } from "@/lib/api/endpoints";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function CopilotPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Merhaba! Stok, satış, müşteri veya finans hakkında soru sorabilirsin.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSend() {
    if (!input.trim()) return;
    const question = input;
    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setInput("");
    setLoading(true);

    try {
      const answer = await askCopilot(question);
      setMessages((prev) => [...prev, { role: "assistant", content: answer }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Bir hata oluştu, lütfen tekrar dene." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex h-full max-w-2xl flex-col">
      <div className="glass glass-hover mb-4 flex-1 space-y-3 overflow-y-auto">
        <div className="glass-glow -right-16 -top-16 h-56 w-56 bg-indigo-500/20" />
        <div className="glass-glow -left-16 bottom-0 top-auto h-48 w-48 bg-fuchsia-500/15" />
        {messages.map((m, i) => (
          <div
            key={i}
            className={`relative z-10 max-w-md rounded-xl px-4 py-2 text-[13px] ${
              m.role === "user"
                ? "ml-auto bg-gradient-to-br from-sky-500 via-indigo-500 to-fuchsia-500 text-white shadow-glow-md"
                : "border border-white/[0.08] bg-white/[0.04] text-slate-200 backdrop-blur"
            }`}
          >
            {m.content}
          </div>
        ))}
        {loading && (
          <div className="relative z-10 flex items-center gap-1.5 text-[11px] text-sky-300/70">
            <Sparkles size={12} className="animate-pulse" />
            Copilot yazıyor...
          </div>
        )}
      </div>

      <div className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Örn: Hangi ürünler stok riski altında?"
          className="flex-1 rounded-xl border border-white/[0.08] bg-white/[0.04] px-3 py-2.5 text-[13px] text-white placeholder:text-slate-500 backdrop-blur focus:outline-none focus:ring-2 focus:ring-sky-400/40"
        />
        <button
          onClick={handleSend}
          className="flex items-center gap-1 rounded-xl bg-gradient-to-br from-sky-500 via-indigo-500 to-fuchsia-500 px-4 py-2.5 text-[13px] text-white shadow-glow-md transition-transform hover:scale-105"
        >
          <Send size={15} />
        </button>
      </div>
    </div>
  );
}
