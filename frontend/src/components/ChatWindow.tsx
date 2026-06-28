import { useEffect, useRef, useState } from "react";
import { api, type ChatMessageItem } from "../api/client";
import { Button, Spinner } from "./ui";

export function ChatWindow() {
  const [messages, setMessages] = useState<ChatMessageItem[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [error, setError] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api
      .getChatHistory()
      .then((data) => setMessages(data.messages))
      .catch(() => setMessages([]))
      .finally(() => setInitialLoading(false));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const send = async () => {
    const text = input.trim();
    if (!text || loading) return;

    setInput("");
    setError("");
    setLoading(true);

    const userMsg: ChatMessageItem = {
      role: "user",
      content: text,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);

    const assistantMsg: ChatMessageItem = {
      role: "assistant",
      content: "",
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, assistantMsg]);

    try {
      let full = "";
      for await (const chunk of api.streamChat(text)) {
        full += chunk;
        setMessages((prev) => {
          const copy = [...prev];
          copy[copy.length - 1] = { ...assistantMsg, content: full };
          return copy;
        });
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка чата");
      setMessages((prev) => prev.slice(0, -1));
    } finally {
      setLoading(false);
    }
  };

  if (initialLoading) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 space-y-4 overflow-y-auto p-4 md:p-6">
        {messages.length === 0 && (
          <div className="rounded-2xl bg-brand-50 p-4 text-sm text-brand-700">
            Задайте вопрос о развитии малыша, играх или шкале Гриффитс. Ответы
            генерируются через NordRouter.
          </div>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
                msg.role === "user"
                  ? "bg-brand-600 text-white"
                  : "border border-slate-200 bg-white text-slate-800"
              }`}
            >
              {msg.content || (loading && i === messages.length - 1 ? "…" : "")}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {error && (
        <p className="px-4 text-sm text-red-600 md:px-6">{error}</p>
      )}

      <div className="border-t border-slate-200 bg-white p-4">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                send();
              }
            }}
            placeholder="Спросите нейроконсультанта…"
            rows={2}
            className="flex-1 resize-none rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none ring-brand-500 focus:ring-2"
          />
          <Button onClick={send} disabled={loading || !input.trim()}>
            {loading ? <Spinner /> : "Отправить"}
          </Button>
        </div>
      </div>
    </div>
  );
}
