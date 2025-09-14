import { useState } from "react";
import { Send } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export default function ChatArea() {
  const [messages, setMessages] = useState<{role: string; text: string}[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    
    const userMessage = input.trim();
    setMessages(prev => [...prev, { role: "user", text: userMessage }]);
    setInput("");
    setLoading(true);

    try {
      const response = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: userMessage
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get response');
      }

      const data = await response.json();
      setMessages(prev => [...prev, { role: "assistant", text: data.reply }]);
    } catch (error) {
      console.error("Chat error:", error);
      setMessages(prev => [...prev, { 
        role: "assistant", 
        text: "Sorry, I'm having trouble connecting to the AI service. Please make sure the backend is running." 
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <Card className="w-full h-full flex flex-col">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          🤖 AI Assistant
        </CardTitle>
        <p className="text-sm text-gray-600">
          Get real-time help and insights from your AI copilot
        </p>
      </CardHeader>

      <CardContent className="flex flex-col flex-1">
        <div className="flex-1 overflow-y-auto space-y-3 p-2 border rounded-md bg-gray-50 min-h-[300px]">
          {messages.length === 0 && (
            <div className="text-center text-gray-500 text-sm py-8">
              Start a conversation with your AI assistant!
            </div>
          )}
          {messages.map((m, i) => (
            <div
              key={i}
              className={`p-3 rounded-md text-sm max-w-[80%] ${
                m.role === "user" 
                  ? "bg-blue-100 ml-auto" 
                  : "bg-white border"
              }`}
            >
              <div className="font-medium text-xs text-gray-500 mb-1">
                {m.role === "user" ? "You" : "AI Assistant"}
              </div>
              <div className="whitespace-pre-wrap">{m.text}</div>
            </div>
          ))}
          {loading && (
            <div className="p-3 rounded-md text-sm bg-white border max-w-[80%]">
              <div className="font-medium text-xs text-gray-500 mb-1">AI Assistant</div>
              <div className="flex items-center gap-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                <span className="text-gray-500">Thinking...</span>
              </div>
            </div>
          )}
        </div>

        <div className="flex gap-2 mt-3">
          <Input
            placeholder="Type your question..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={loading}
          />
          <Button onClick={sendMessage} disabled={loading || !input.trim()}>
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
