import { useState } from "react";

interface ChatBoxProps {
  schema: any;
  logs: any;
}

export default function ChatBox({ schema, logs }: ChatBoxProps) {
  const [messages, setMessages] = useState<{ role: string; content: string }[]>(
    []
  );
  const [input, setInput] = useState("");

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMsg = { role: "user", content: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");

    try {
      const res = await fetch("http://localhost:8000/llm-chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: input,
          schema,
          logs,
        }),
      });
      const data = await res.json();
      const botMsg = { role: "assistant", content: data.reply };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="bg-white rounded-xl border shadow-md p-6 max-w-3xl mx-auto">
      <h2 className="text-lg font-semibold mb-3 text-gray-800">
        💬 AI Assistant
      </h2>
      <div className="h-64 overflow-y-auto border rounded-md p-3 mb-3 bg-gray-50 space-y-2">
        {messages.map((m, i) => (
          <div
            key={i}
            className={`p-2 rounded-md text-sm ${
              m.role === "user"
                ? "bg-blue-100 text-blue-800 self-end"
                : "bg-gray-200 text-gray-800"
            }`}
          >
            <strong>{m.role === "user" ? "You: " : "AI: "}</strong>
            {m.content}
          </div>
        ))}
      </div>
      <div className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          placeholder="Ask about performance bottlenecks..."
          className="flex-1 border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring focus:ring-blue-300"
        />
        <button
          onClick={sendMessage}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
        >
          Send
        </button>
      </div>
    </div>
  );
}
