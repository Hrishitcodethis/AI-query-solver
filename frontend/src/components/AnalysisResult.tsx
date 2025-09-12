import { Brain, Lightbulb, AlertTriangle, CheckCircle, TrendingUp } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface AnalysisResultProps {
  analysis: string;
}

export default function AnalysisResult({ analysis }: AnalysisResultProps) {
  // Parse analysis to extract different sections
  const parseAnalysis = (text: string) => {
    const sections = {
      summary: '',
      optimizations: [] as string[],
      warnings: [] as string[],
      recommendations: [] as string[]
    };

    // Simple parsing logic - in a real app, this would be more sophisticated
    const lines = text.split('\n').filter(line => line.trim());
    
    let currentSection = 'summary';
    
    lines.forEach(line => {
      const trimmedLine = line.trim();
      
      if (trimmedLine.toLowerCase().includes('optimization') || trimmedLine.toLowerCase().includes('optimize')) {
        currentSection = 'optimizations';
      } else if (trimmedLine.toLowerCase().includes('warning') || trimmedLine.toLowerCase().includes('caution')) {
        currentSection = 'warnings';
      } else if (trimmedLine.toLowerCase().includes('recommend') || trimmedLine.toLowerCase().includes('suggest')) {
        currentSection = 'recommendations';
      }
      
      if (trimmedLine.startsWith('- ') || trimmedLine.startsWith('• ')) {
        const cleanLine = trimmedLine.substring(2);
        if (currentSection === 'optimizations') {
          sections.optimizations.push(cleanLine);
        } else if (currentSection === 'warnings') {
          sections.warnings.push(cleanLine);
        } else if (currentSection === 'recommendations') {
          sections.recommendations.push(cleanLine);
        }
      } else if (currentSection === 'summary' && trimmedLine.length > 0) {
        sections.summary += (sections.summary ? ' ' : '') + trimmedLine;
      }
    });

    // If no structured data found, treat everything as summary
    if (!sections.optimizations.length && !sections.warnings.length && !sections.recommendations.length) {
      sections.summary = text;
    }

    return sections;
  };

  const parsedAnalysis = parseAnalysis(analysis);

  return (
    <div className="w-full space-y-4 sm:space-y-6">
      {/* Main Analysis Card */}
      <Card className="border-l-4 border-l-blue-500">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-blue-600" />
            AI Analysis Results
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 sm:space-y-4">
          {parsedAnalysis.summary && (
            <div className="p-3 sm:p-4 bg-blue-50 rounded-lg">
              <h3 className="font-semibold text-blue-900 mb-2">Summary</h3>
              <p className="text-sm sm:text-base text-blue-800 leading-relaxed">{parsedAnalysis.summary}</p>
            </div>
          )}

          {/* Raw analysis if no structured parsing */}
          {!parsedAnalysis.summary && (
            <div className="p-3 sm:p-4 bg-gray-50 rounded-lg">
              <p className="text-sm sm:text-base text-gray-800 leading-relaxed whitespace-pre-wrap break-words">{analysis}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Structured Results */}
      {(parsedAnalysis.optimizations.length > 0 || parsedAnalysis.warnings.length > 0 || parsedAnalysis.recommendations.length > 0) && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
          {/* Optimizations */}
          {parsedAnalysis.optimizations.length > 0 && (
            <Card className="border-l-4 border-l-green-500 sm:col-span-2 lg:col-span-1">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base sm:text-lg">
                  <TrendingUp className="w-5 h-5 text-green-600" />
                  Optimizations
                  <Badge variant="secondary" className="ml-2 bg-green-100 text-green-800">
                    {parsedAnalysis.optimizations.length}
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 sm:space-y-3">
                  {parsedAnalysis.optimizations.map((optimization, index) => (
                    <div key={index} className="flex items-start gap-2 sm:gap-3 p-2 sm:p-3 bg-green-50 rounded-lg">
                      <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                      <p className="text-xs sm:text-sm text-green-800 break-words">{optimization}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Warnings */}
          {parsedAnalysis.warnings.length > 0 && (
            <Card className="border-l-4 border-l-yellow-500 sm:col-span-2 lg:col-span-1">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base sm:text-lg">
                  <AlertTriangle className="w-5 h-5 text-yellow-600" />
                  Warnings
                  <Badge variant="secondary" className="ml-2 bg-yellow-100 text-yellow-800">
                    {parsedAnalysis.warnings.length}
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 sm:space-y-3">
                  {parsedAnalysis.warnings.map((warning, index) => (
                    <div key={index} className="flex items-start gap-2 sm:gap-3 p-2 sm:p-3 bg-yellow-50 rounded-lg">
                      <AlertTriangle className="w-4 h-4 text-yellow-600 mt-0.5 flex-shrink-0" />
                      <p className="text-xs sm:text-sm text-yellow-800 break-words">{warning}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Recommendations */}
          {parsedAnalysis.recommendations.length > 0 && (
            <Card className="border-l-4 border-l-purple-500 sm:col-span-2 lg:col-span-1">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base sm:text-lg">
                  <Lightbulb className="w-5 h-5 text-purple-600" />
                  Recommendations
                  <Badge variant="secondary" className="ml-2 bg-purple-100 text-purple-800">
                    {parsedAnalysis.recommendations.length}
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 sm:space-y-3">
                  {parsedAnalysis.recommendations.map((recommendation, index) => (
                    <div key={index} className="flex items-start gap-2 sm:gap-3 p-2 sm:p-3 bg-purple-50 rounded-lg">
                      <Lightbulb className="w-4 h-4 text-purple-600 mt-0.5 flex-shrink-0" />
                      <p className="text-xs sm:text-sm text-purple-800 break-words">{recommendation}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}