import { useState } from "react";
import { Send, X, Maximize2 } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";

interface Message {
  role: string;
  text: string;
  graph_url?: string;
  query_id?: number;
  query_text?: string;
}

export default function ChatArea() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [selectedGraph, setSelectedGraph] = useState<{url: string, queryId: number} | null>(null);

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
      setMessages(prev => [...prev, { 
        role: "assistant", 
        text: data.reply,
        graph_url: data.graph_url,
        query_id: data.query_id,
        query_text: data.query_text
      }]);
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

  const openGraphModal = (graphUrl: string, queryId: number) => {
    setSelectedGraph({ url: graphUrl, queryId });
  };

  const closeGraphModal = () => {
    setSelectedGraph(null);
  };

  const formatText = (text: string) => {
    // Convert **text** to <strong>text</strong> for proper HTML rendering
    return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  };

  return (
    <>
      <Card className="w-full h-[800px] flex flex-col">
        <CardHeader className="flex-shrink-0">
          <CardTitle className="flex items-center gap-2">
            AI Assistant
          </CardTitle>
          <p className="text-sm text-gray-600">
            Get real-time help and insights from your AI copilot
          </p>
        </CardHeader>

        <CardContent className="flex flex-col flex-1 min-h-0 p-4">
          <div className="flex-1 overflow-y-auto space-y-3 p-2 border rounded-md bg-gray-50">
            {messages.length === 0 && (
              <div className="text-center text-gray-500 text-sm py-8">
                Start a conversation with your AI assistant!
                <br />
                <span className="text-xs mt-2 block">
                  Try: "analyze query 22" or "show graph for query 1"
                </span>
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
                
                {/* Show query text if available */}
                {m.query_text && (
                  <div className="mb-2 p-2 bg-gray-100 rounded text-xs font-mono">
                    <div className="font-medium text-gray-600 mb-1">Query:</div>
                    <div className="text-gray-800 whitespace-pre-wrap">{m.query_text}</div>
                  </div>
                )}
                
                <div 
                  className="whitespace-pre-wrap"
                  dangerouslySetInnerHTML={{ __html: formatText(m.text) }}
                />
                
                {/* Graph Display */}
                {m.graph_url && (
                  <div className="mt-3 border rounded-lg overflow-hidden">
                    <div className="bg-gray-100 px-3 py-2 text-xs font-medium text-gray-600 flex items-center justify-between">
                      <span>📊 Performance Graph - Query {m.query_id}</span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => openGraphModal(m.graph_url!, m.query_id!)}
                        className="h-6 w-6 p-0 hover:bg-gray-200"
                      >
                        <Maximize2 className="h-3 w-3" />
                      </Button>
                    </div>
                    <iframe
                      src={m.graph_url}
                      className="w-full h-64 border-0 cursor-pointer"
                      title={`Query ${m.query_id} Performance Graph`}
                      onClick={() => openGraphModal(m.graph_url!, m.query_id!)}
                    />
                  </div>
                )}
              </div>
            ))}
            {loading && (
              <div className="p-3 rounded-md text-sm bg-white border max-w-[80%]">
                <div className="font-medium text-xs text-gray-500 mb-1">AI Assistant</div>
                <div className="flex items-center gap-2">
                  <div className="animate-spin rounded-full h-4 h-4 border-b-2 border-blue-600"></div>
                  <span className="text-gray-500">Thinking...</span>
                </div>
              </div>
            )}
          </div>

          <div className="flex gap-2 mt-3 flex-shrink-0">
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

      {/* Graph Modal */}
      <Dialog open={!!selectedGraph} onOpenChange={closeGraphModal}>
        <DialogContent className="max-w-6xl max-h-[90vh] p-0">
          <DialogHeader className="p-6 pb-0">
            <DialogTitle className="flex items-center justify-between">
              <span>📊 Performance Graph - Query {selectedGraph?.queryId}</span>
              <Button
                variant="ghost"
                size="sm"
                onClick={closeGraphModal}
                className="h-8 w-8 p-0"
              >
                <X className="h-4 w-4" />
              </Button>
            </DialogTitle>
          </DialogHeader>
          <div className="p-6 pt-0">
            {selectedGraph && (
              <iframe
                src={selectedGraph.url}
                className="w-full h-[70vh] border rounded-lg"
                title={`Query ${selectedGraph.queryId} Performance Graph - Full View`}
              />
            )}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
