import { useState } from "react";
import { Upload, Database, FileText, CheckCircle, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

interface UploadSectionProps {
  onSchemaLoaded: (schema: any) => void;
  onLogsLoaded: (logs: any) => void;
}

export default function UploadSection({ onSchemaLoaded, onLogsLoaded }: UploadSectionProps) {
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [dbFile, setDbFile] = useState<File | null>(null);
  const [logFile, setLogFile] = useState<File | null>(null);

  const uploadFiles = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!dbFile || !logFile) return;

    setUploading(true);
    setUploadStatus('idle');

    try {
      const formData = new FormData();
      formData.append("db_file", dbFile);
      formData.append("log_file", logFile);

      const res = await fetch("http://localhost:8000/upload", {
        method: "POST",
        body: formData
      });
      
      if (!res.ok) throw new Error('Upload failed');
      
      const data = await res.json();
      onSchemaLoaded(data.schema);
      onLogsLoaded(data.logs);
      setUploadStatus('success');
    } catch (error) {
      console.error("Upload error:", error);
      setUploadStatus('error');
    } finally {
      setUploading(false);
    }
  };

  return (
    <Card className="w-full">
      <CardHeader className="text-center">
        <CardTitle className="flex items-center justify-center gap-2">
          <Upload className="w-5 h-5" />
          Upload Database Files
        </CardTitle>
        <CardDescription>
          Upload your database file (.db) and query log file (.csv) to start analyzing
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={uploadFiles} className="space-y-4 sm:space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
            {/* Database File Upload */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                <Database className="w-4 h-4" />
                Database File (.db)
              </label>
              <div className="relative">
                <input
                  type="file"
                  accept=".db"
                  onChange={(e) => setDbFile(e.target.files?.[0] || null)}
                  className="hidden"
                  id="db-file"
                  required
                />
                <label
                  htmlFor="db-file"
                  className="flex items-center justify-center w-full h-24 sm:h-32 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:border-blue-400 hover:bg-blue-50 transition-colors"
                >
                  <div className="text-center">
                    <Database className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                    {dbFile ? (
                      <div>
                        <p className="text-sm font-medium text-green-600">{dbFile.name}</p>
                        <p className="text-xs text-gray-500">{Math.round(dbFile.size / 1024)} KB</p>
                      </div>
                    ) : (
                      <div>
                        <p className="text-xs sm:text-sm text-gray-600">Click to select database file</p>
                        <p className="text-xs text-gray-400">SQLite .db files</p>
                      </div>
                    )}
                  </div>
                </label>
              </div>
            </div>

            {/* Log File Upload */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                <FileText className="w-4 h-4" />
                Log File (.csv)
              </label>
              <div className="relative">
                <input
                  type="file"
                  accept=".csv"
                  onChange={(e) => setLogFile(e.target.files?.[0] || null)}
                  className="hidden"
                  id="log-file"
                  required
                />
                <label
                  htmlFor="log-file"
                  className="flex items-center justify-center w-full h-24 sm:h-32 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:border-blue-400 hover:bg-blue-50 transition-colors"
                >
                  <div className="text-center">
                    <FileText className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                    {logFile ? (
                      <div>
                        <p className="text-sm font-medium text-green-600">{logFile.name}</p>
                        <p className="text-xs text-gray-500">{Math.round(logFile.size / 1024)} KB</p>
                      </div>
                    ) : (
                      <div>
                        <p className="text-xs sm:text-sm text-gray-600">Click to select log file</p>
                        <p className="text-xs text-gray-400">CSV format</p>
                      </div>
                    )}
                  </div>
                </label>
              </div>
            </div>
          </div>

          {/* Upload Button */}
          <div className="flex flex-col items-center gap-4">
            <Button
              type="submit"
              disabled={!dbFile || !logFile || uploading}
              size="lg"
              className="w-full sm:w-auto"
            >
              {uploading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4 mr-2" />
                  Upload Files
                </>
              )}
            </Button>

            {/* Status Messages */}
            {uploadStatus === 'success' && (
              <div className="flex items-center gap-2 text-green-600">
                <CheckCircle className="w-4 h-4" />
                <span className="text-sm">Files uploaded successfully!</span>
              </div>
            )}
            {uploadStatus === 'error' && (
              <div className="flex items-center gap-2 text-red-600">
                <AlertCircle className="w-4 h-4" />
                <span className="text-sm">Upload failed. Please try again.</span>
              </div>
            )}
          </div>
        </form>
      </CardContent>
    </Card>
  );
}