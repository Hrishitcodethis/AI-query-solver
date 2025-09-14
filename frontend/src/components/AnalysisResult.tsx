import { CheckCircle, Copy } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface AnalysisResultProps {
  analysis: string;
}

export default function AnalysisResult({ analysis }: AnalysisResultProps) {
  const copyToClipboard = () => {
    navigator.clipboard.writeText(analysis);
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CheckCircle className="w-5 h-5 text-green-600" />
          Query Execution Result
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <p className="text-sm text-green-800">{analysis}</p>
          </div>
          
          <div className="flex justify-end">
            <Button
              variant="outline"
              size="sm"
              onClick={copyToClipboard}
              className="text-xs"
            >
              <Copy className="w-3 h-3 mr-1" />
              Copy Result
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}