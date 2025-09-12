import { useState } from "react";
import { Search, Zap, AlertCircle, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";

interface QueryFormProps {
  onAnalysis: (result: { analysis: string; updated_logs: any[] }) => void;
}

export default function QueryForm({ onAnalysis }: QueryFormProps) {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle');

  const submitQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setStatus('idle');

    try {
      const res = await fetch("http://localhost:8000/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: query.trim() })
      });

      if (!res.ok) throw new Error('Analysis failed');
      
      const data = await res.json();
      onAnalysis(data);
      setStatus('success');
    } catch (error) {
      console.error("Analysis error:", error);
      setStatus('error');
    } finally {
      setLoading(false);
    }
  };

  const exampleQueries = [
    "SELECT * FROM users WHERE age > 25",
    "SELECT COUNT(*) FROM orders GROUP BY status",
    "SELECT u.name, o.total FROM users u JOIN orders o ON u.id = o.user_id",
    "UPDATE products SET price = price * 1.1 WHERE category = 'electronics'"
  ];

  const handleExampleClick = (exampleQuery: string) => {
    setQuery(exampleQuery);
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Search className="w-5 h-5 text-blue-600" />
          SQL Query Analyzer
        </CardTitle>
        <p className="text-sm text-gray-600">
          Enter your SQL query to get AI-powered optimization insights
        </p>
      </CardHeader>
      <CardContent className="space-y-4 sm:space-y-6">
        <form onSubmit={submitQuery} className="space-y-3 sm:space-y-4">
          <div className="space-y-2">
            <label htmlFor="query" className="text-sm font-medium text-gray-700">
              SQL Query
            </label>
            <Textarea
              id="query"
              placeholder="Enter your SQL query here..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="min-h-[100px] sm:min-h-[120px] font-mono text-sm w-full resize-none"
              required
            />
          </div>

          <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
            <Button
              type="submit"
              disabled={!query.trim() || loading}
              className="w-full sm:w-auto"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Zap className="w-4 h-4 mr-2" />
                  Analyze Query
                </>
              )}
            </Button>

            {status === 'success' && (
              <div className="flex items-center justify-center sm:justify-start gap-2 text-green-600">
                <CheckCircle className="w-4 h-4" />
                <span className="text-sm">Analysis complete!</span>
              </div>
            )}
            {status === 'error' && (
              <div className="flex items-center justify-center sm:justify-start gap-2 text-red-600">
                <AlertCircle className="w-4 h-4" />
                <span className="text-sm">Analysis failed. Please try again.</span>
              </div>
            )}
          </div>
        </form>

        {/* Example Queries */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-gray-700">Example Queries</h3>
          <div className="space-y-2">
            {exampleQueries.map((example, index) => (
              <button
                key={index}
                type="button"
                onClick={() => handleExampleClick(example)}
                className="w-full text-left p-2 sm:p-3 text-xs sm:text-sm bg-gray-50 hover:bg-gray-100 rounded-lg border border-gray-200 transition-colors font-mono break-all"
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}