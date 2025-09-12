import { useState } from "react";
import UploadSection from "./components/UploadSection";
import SchemaExplorer from "./components/SchemaExplorer";
import QueryForm from "./components/QueryForm";
import AnalyticsCharts from "./components/AnalyticsCharts";
import AnalysisResult from "./components/AnalysisResult";
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
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 w-full">
      <div className="w-full px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8">
        {/* Header */}
        <div className="text-center mb-6 sm:mb-8 lg:mb-12">
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="p-3 bg-blue-600 rounded-xl shadow-lg">
              <Database className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-gray-900">
              AI-Powered DB Profiler
            </h1>
          </div>
          <p className="text-sm sm:text-base lg:text-lg text-gray-600 max-w-2xl mx-auto px-4">
            Upload your database and log files to get intelligent insights, performance analytics, and query optimization recommendations powered by AI.
          </p>
        </div>

        {/* Upload Section */}
        <div className="mb-6 sm:mb-8">
          <UploadSection onSchemaLoaded={setSchema} onLogsLoaded={setLogs} />
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 lg:gap-8 mb-6 sm:mb-8">
          {/* Schema Explorer */}
          {schema && (
            <div className="w-full">
              <SchemaExplorer schema={schema} />
            </div>
          )}

          {/* Analytics Charts */}
          {logs && (
            <div className="w-full">
              <AnalyticsCharts logs={logs} />
            </div>
          )}
        </div>

        {/* Query Analysis Section */}
        <div className="w-full space-y-6 lg:space-y-0 lg:grid lg:grid-cols-12 lg:gap-6">
          <div className="w-full lg:col-span-5 xl:col-span-4">
            <QueryForm
              onAnalysis={(res) => {
                setAnalysis(res.analysis);
                setLogs(res.updated_logs);
              }}
            />
          </div>
          
          {analysis && (
            <div className="w-full lg:col-span-7 xl:col-span-8">
              <AnalysisResult analysis={analysis} />
            </div>
          )}
        </div>

        {/* Stats Section */}
        {(schema || logs) && (
          <div className="mt-8 sm:mt-12 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
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
                  <p className="text-sm font-medium text-gray-600">Log Entries</p>
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
                  <p className="text-sm font-medium text-gray-600">Avg Response</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {logs ? `${Math.round(logs.reduce((acc, log) => acc + log.exec_time_ms, 0) / logs.length)}ms` : '0ms'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}