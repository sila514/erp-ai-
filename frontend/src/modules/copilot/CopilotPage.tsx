import { useState } from "react";
import { Send } from "lucide-react";
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
    <div className="flex flex-col h-full max-w-2xl">
      <h1 className="text-xl font-semibold text-gray-900 mb-4">AI Copilot</h1>

      <div className="flex-1 space-y-3 overflow-y-auto mb-4">
        {messages.map((m, i) => (
          <div
            key={i}
            className={`rounded-xl px-4 py-2 text-sm max-w-md ${
              m.role === "user"
                ? "bg-brand-600 text-white ml-auto"
                : "bg-white border border-gray-200 text-gray-800"
            }`}
          >
            {m.content}
          </div>
        ))}
        {loading && <p className="text-xs text-gray-400">Copilot yazıyor...</p>}
      </div>

      <div className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Örn: Hangi ürünler stok riski altında?"
          className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
        />
        <button
          onClick={handleSend}
          className="bg-brand-600 text-white rounded-lg px-4 py-2 flex items-center gap-1 text-sm"
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  );
}
