import { useState } from "react";
import UploadSection from "./components/UploadSection";
import SchemaExplorer from "./components/SchemaExplorer";
import QueryForm from "./components/QueryForm";
import AnalyticsCharts from "./components/AnalyticsCharts";
import AnalysisResult from "./components/AnalysisResult";
import ChatArea from "./components/ChatArea";
import { Database, Activity, Zap } from "lucide-react";

interface Schema {
  [tableName: string]: {
    columns: Array<{
      name: string;
      type: string;
    }>;
    sample_values: {
      [columnName: string]: string[];
    };
  };
}

interface LogEntry {
  timestamp: string;
  exec_time_ms: number;
  query: string;
}

export default function App() {
  const [schema, setSchema] = useState<Schema | null>(null);
  const [logs, setLogs] = useState<LogEntry[] | null>(null);
  const [analysis, setAnalysis] = useState<string | null>(null);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 w-full px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8">
      {/* Header */}
      <div className="text-center mb-6 sm:mb-8">
        <div className="flex items-center justify-center gap-3 mb-4">
          <div className="p-3 bg-blue-600 rounded-xl shadow-lg">
            <Database className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-gray-900">
            AI-Powered DB Profiler
          </h1>
        </div>
        <p className="text-sm sm:text-base lg:text-lg text-gray-600 max-w-2xl mx-auto px-4">
          Upload your database and log files to get intelligent insights,
          performance analytics, and query optimization recommendations powered
          by AI.
        </p>
      </div>

      {/* Main Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-[70%_30%] gap-6">
        {/* LEFT COLUMN */}
        <div className="space-y-6">
          {/* Upload Section */}
          <UploadSection onSchemaLoaded={setSchema} onLogsLoaded={setLogs} />

          {/* SQL Analyzer */}
          <div className="space-y-6">
            <QueryForm
              onAnalysis={(res) => {
                setAnalysis(res.analysis);
                setLogs(res.updated_logs);
              }}
            />
            {analysis && <AnalysisResult analysis={analysis} />}
          </div>

          {/* Extra Tools (Schema Explorer + Analytics) */}
          {(schema || logs) && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {schema && <SchemaExplorer schema={schema} />}
              {logs && <AnalyticsCharts logs={logs} />}
            </div>
          )}

          {/* Stats Section */}
          {(schema || logs) && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <Database className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-600">Tables</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {schema ? Object.keys(schema).length : 0}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <Activity className="w-5 h-5 text-green-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-600">
                      Log Entries
                    </p>
                    <p className="text-2xl font-bold text-gray-900">
                      {logs ? logs.length : 0}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-yellow-100 rounded-lg">
                    <Zap className="w-5 h-5 text-yellow-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-600">
                      Avg Response
                    </p>
                    <p className="text-2xl font-bold text-gray-900">
                      {logs
                        ? `${Math.round(
                            logs.reduce(
                              (acc, log) => acc + log.exec_time_ms,
                              0
                            ) / logs.length
                          )}ms`
                        : "0ms"}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* RIGHT COLUMN: Chat Area */}
        <div className="h-full">
          <ChatArea schema={schema} logs={logs} />
        </div>
      </div>
    </div>
  );
}
