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
      <div className="card-dark mb-4 flex-1 space-y-3 overflow-y-auto">
        {messages.map((m, i) => (
          <div
            key={i}
            className={`max-w-md rounded-xl px-4 py-2 text-[13px] ${
              m.role === "user"
                ? "ml-auto bg-gradient-to-br from-sky-500 to-blue-600 text-white shadow-glow-sm"
                : "border border-sky-400/15 bg-navy-900/60 text-sky-100/85"
            }`}
          >
            {m.content}
          </div>
        ))}
        {loading && (
          <div className="flex items-center gap-1.5 text-[11px] text-sky-400/50">
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
          className="flex-1 rounded-lg border border-sky-400/20 bg-navy-900/60 px-3 py-2 text-[13px] text-sky-100 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-400/40"
        />
        <button
          onClick={handleSend}
          className="flex items-center gap-1 rounded-lg bg-gradient-to-br from-sky-500 to-blue-600 px-4 py-2 text-[13px] text-white shadow-glow-sm transition-opacity hover:opacity-90"
        >
          <Send size={15} />
        </button>
      </div>
    </div>
  );
}
