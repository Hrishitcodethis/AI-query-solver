import { useState } from "react";
import { Search, Zap, AlertCircle, CheckCircle, Copy } from "lucide-react";
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
  const [queryId, setQueryId] = useState<string | null>(null);
  const [executionTime, setExecutionTime] = useState<number | null>(null);
  const [rowsReturned, setRowsReturned] = useState<number | null>(null);

  const copyQueryId = () => {
    if (queryId) {
      navigator.clipboard.writeText(queryId);
    }
  };

  const submitQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setStatus('idle');
    setQueryId(null);

    try {
      const res = await fetch("http://localhost:8000/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: query.trim() })
      });

      if (!res.ok) throw new Error('Query execution failed');
      
      const data = await res.json();
      
      // Update state with query results
      setQueryId(data.query_id);
      setExecutionTime(data.execution_time);
      setRowsReturned(data.rows_returned);
      
      // Call the parent callback with minimal data
      onAnalysis({
        analysis: data.message,
        updated_logs: [] // No logs needed for display
      });
      
      setStatus('success');
    } catch (error) {
      console.error("Query execution error:", error);
      setStatus('error');
    } finally {
      setLoading(false);
    }
  };

  const exampleQueries = [
    "SELECT COUNT(*) FROM customer",
    "SELECT * FROM store_sales LIMIT 10",
    "SELECT i_category, SUM(ss_sales_price) FROM store_sales ss JOIN item i ON ss.ss_item_sk = i.i_item_sk GROUP BY i_category",
    "SELECT c_first_name, c_last_name FROM customer WHERE c_customer_sk < 100"
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
          Execute your SQL query and get a query ID for analysis
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
                  Executing...
                </>
              ) : (
                <>
                  <Zap className="w-4 h-4 mr-2" />
                  Execute Query
                </>
              )}
            </Button>

            {status === 'success' && queryId && (
              <div className="flex items-center gap-2 text-green-600">
                <CheckCircle className="w-4 h-4" />
                <span className="text-sm">Query executed! ID: {queryId}</span>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={copyQueryId}
                  className="h-6 px-2 text-xs"
                >
                  <Copy className="w-3 h-3 mr-1" />
                  Copy ID
                </Button>
              </div>
            )}
            {status === 'error' && (
              <div className="flex items-center gap-2 text-red-600">
                <AlertCircle className="w-4 h-4" />
                <span className="text-sm">Query failed. Please try again.</span>
              </div>
            )}
          </div>

          {/* Query Results */}
          {status === 'success' && queryId && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-3">
              <div className="text-sm text-green-800">
                <p><strong>Query ID:</strong> {queryId}</p>
                <p><strong>Execution Time:</strong> {executionTime?.toFixed(2)}ms</p>
                <p><strong>Rows Returned:</strong> {rowsReturned}</p>
                <p className="mt-2 text-xs text-green-600">
                   Ask the AI assistant: "analyze query {queryId}" for detailed analysis
                </p>
              </div>
            </div>
          )}
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