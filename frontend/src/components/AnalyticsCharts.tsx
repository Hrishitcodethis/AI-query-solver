import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from "recharts";
import { Activity, TrendingUp, Clock, AlertTriangle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface LogEntry {
  timestamp: string;
  exec_time_ms: number;
  query: string;
}

interface AnalyticsChartsProps {
  logs: LogEntry[];
}

export default function AnalyticsCharts({ logs }: AnalyticsChartsProps) {
  // Prepare data for different visualizations
  const sortedLogs = [...logs].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
  
  // Performance distribution data
  const performanceRanges = [
    { range: '0-10ms', count: 0, color: '#10B981' },
    { range: '10-50ms', count: 0, color: '#3B82F6' },
    { range: '50-100ms', count: 0, color: '#F59E0B' },
    { range: '100ms+', count: 0, color: '#EF4444' }
  ];

  logs.forEach(log => {
    if (log.exec_time_ms <= 10) performanceRanges[0].count++;
    else if (log.exec_time_ms <= 50) performanceRanges[1].count++;
    else if (log.exec_time_ms <= 100) performanceRanges[2].count++;
    else performanceRanges[3].count++;
  });

  // Calculate statistics
  const avgTime = logs.reduce((sum, log) => sum + log.exec_time_ms, 0) / logs.length;
  const maxTime = Math.max(...logs.map(log => log.exec_time_ms));
  const slowQueries = logs.filter(log => log.exec_time_ms > 100).length;

  // Format data for time series chart
  const timeSeriesData = sortedLogs.map((log, index) => ({
    ...log,
    index,
    formattedTime: new Date(log.timestamp).toLocaleTimeString()
  }));

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="text-sm text-gray-600">{`Time: ${payload[0].payload.formattedTime}`}</p>
          <p className="text-sm font-medium text-blue-600">
            {`Execution Time: ${payload[0].value}ms`}
          </p>
          <p className="text-xs text-gray-500 mt-1 max-w-xs truncate">
            {`Query: ${payload[0].payload.query}`}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full space-y-4 sm:space-y-6">
      {/* Stats Overview */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
        <Card>
          <CardContent className="p-3 sm:p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <TrendingUp className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">Avg Time</p>
                <p className="text-xl sm:text-2xl font-bold text-gray-900">{avgTime.toFixed(1)}ms</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-3 sm:p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <Clock className="w-5 h-5 text-yellow-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">Max Time</p>
                <p className="text-xl sm:text-2xl font-bold text-gray-900">{maxTime}ms</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-3 sm:p-4 sm:col-span-2 lg:col-span-1">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-red-100 rounded-lg">
                <AlertTriangle className="w-5 h-5 text-red-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">Slow Queries</p>
                <p className="text-xl sm:text-2xl font-bold text-gray-900">{slowQueries}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Performance Timeline */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-blue-600" />
            Query Performance Timeline
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 sm:h-80 w-full overflow-hidden">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={timeSeriesData}>
                <XAxis 
                  dataKey="index" 
                  tickFormatter={(value) => `#${value + 1}`}
                  stroke="#6B7280"
                  fontSize={12}
                />
                <YAxis 
                  stroke="#6B7280"
                  tickFormatter={(value) => `${value}ms`}
                  fontSize={12}
                />
                <Tooltip content={<CustomTooltip />} />
                <CartesianGrid stroke="#F3F4F6" strokeDasharray="3 3" />
                <Line 
                  type="monotone" 
                  dataKey="exec_time_ms" 
                  stroke="#3B82F6" 
                  strokeWidth={2}
                  dot={{ fill: '#3B82F6', strokeWidth: 2, r: 4 }}
                  activeDot={{ r: 6, stroke: '#3B82F6', strokeWidth: 2 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
        {/* Performance Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Performance Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-48 sm:h-64 w-full overflow-hidden">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={performanceRanges}>
                  <XAxis dataKey="range" stroke="#6B7280" fontSize={12} />
                  <YAxis stroke="#6B7280" fontSize={12} />
                  <Tooltip 
                    formatter={(value) => [`${value} queries`, 'Count']}
                    labelStyle={{ color: '#374151' }}
                  />
                  <CartesianGrid stroke="#F3F4F6" strokeDasharray="3 3" />
                  <Bar 
                    dataKey="count" 
                    fill="#3B82F6"
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Performance Breakdown Pie Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Performance Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-48 sm:h-64 w-full overflow-hidden">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={performanceRanges.filter(range => range.count > 0)}
                    cx="50%"
                    cy="50%"
                    innerRadius={30}
                    outerRadius={60}
                    dataKey="count"
                    label={({ range, count }) => window.innerWidth > 640 ? `${range}: ${count}` : count}
                    fontSize={12}
                  >
                    {performanceRanges.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => [`${value} queries`, 'Count']} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              {performanceRanges.filter(range => range.count > 0).map((range) => (
                <Badge key={range.range} variant="secondary" className="text-xs">
                  <div 
                    className="w-2 h-2 rounded-full mr-2" 
                    style={{ backgroundColor: range.color }}
                  />
                  {range.range}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}