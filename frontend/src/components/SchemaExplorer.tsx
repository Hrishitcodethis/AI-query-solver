import { useState } from "react";
import { Database, Table, ChevronDown, ChevronRight, Hash, Type } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";

interface Column {
  name: string;
  type: string;
}

interface Schema {
  [tableName: string]: {
    columns: Column[];
    sample_values: {
      [columnName: string]: string[];
    };
  };
}

interface SchemaExplorerProps {
  schema: Schema;
}

export default function SchemaExplorer({ schema }: SchemaExplorerProps) {
  const [openTables, setOpenTables] = useState<Set<string>>(new Set());

  const toggleTable = (tableName: string) => {
    const newOpenTables = new Set(openTables);
    if (newOpenTables.has(tableName)) {
      newOpenTables.delete(tableName);
    } else {
      newOpenTables.add(tableName);
    }
    setOpenTables(newOpenTables);
  };

  const getTypeColor = (type: string) => {
    const lowerType = type.toLowerCase();
    if (lowerType.includes('int')) return 'bg-blue-100 text-blue-800';
    if (lowerType.includes('varchar') || lowerType.includes('text') || lowerType.includes('char')) return 'bg-green-100 text-green-800';
    if (lowerType.includes('decimal') || lowerType.includes('float') || lowerType.includes('double')) return 'bg-purple-100 text-purple-800';
    if (lowerType.includes('date') || lowerType.includes('time')) return 'bg-orange-100 text-orange-800';
    if (lowerType.includes('bool')) return 'bg-red-100 text-red-800';
    return 'bg-gray-100 text-gray-800';
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Database className="w-5 h-5 text-blue-600" />
          Database Schema
        </CardTitle>
        <p className="text-xs sm:text-sm text-gray-600">
          {Object.keys(schema).length} tables • Click to expand details
        </p>
      </CardHeader>
      <CardContent className="space-y-3 sm:space-y-4">
        {Object.entries(schema).map(([tableName, info]) => (
          <Collapsible
            key={tableName}
            open={openTables.has(tableName)}
            onOpenChange={() => toggleTable(tableName)}
          >
            <CollapsibleTrigger className="w-full">
              <div className="flex items-center justify-between w-full p-3 sm:p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                <div className="flex items-center gap-3">
                  {openTables.has(tableName) ? (
                    <ChevronDown className="w-4 h-4 text-gray-600" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-gray-600" />
                  )}
                  <Table className="w-5 h-5 text-gray-700" />
                  <h3 className="text-sm sm:text-base font-semibold text-gray-900 truncate">{tableName}</h3>
                </div>
                <Badge variant="secondary" className="ml-2 text-xs">
                  {info.columns.length} columns
                </Badge>
              </div>
            </CollapsibleTrigger>
            
            <CollapsibleContent className="mt-2 sm:mt-3">
              <div className="bg-white border rounded-lg overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50 border-b">
                      <tr>
                        <th className="px-2 sm:px-4 py-2 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          <div className="flex items-center gap-2">
                            <Hash className="w-3 h-3" />
                            Column
                          </div>
                        </th>
                        <th className="px-2 sm:px-4 py-2 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          <div className="flex items-center gap-2">
                            <Type className="w-3 h-3" />
                            Type
                          </div>
                        </th>
                        <th className="px-2 sm:px-4 py-2 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider hidden sm:table-cell">
                          Sample Values
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {info.columns.map((column) => (
                        <tr key={column.name} className="hover:bg-gray-50">
                          <td className="px-2 sm:px-4 py-2 sm:py-3 text-xs sm:text-sm font-medium text-gray-900">
                            {column.name}
                          </td>
                          <td className="px-2 sm:px-4 py-2 sm:py-3 text-xs sm:text-sm">
                            <Badge
                              variant="secondary"
                              className={`${getTypeColor(column.type)} border-0 text-xs`}
                            >
                              {column.type}
                            </Badge>
                          </td>
                          <td className="px-2 sm:px-4 py-2 sm:py-3 text-xs sm:text-sm text-gray-600 hidden sm:table-cell">
                            <div className="max-w-xs truncate break-all">
                              {info.sample_values[column.name]?.length > 0 
                                ? info.sample_values[column.name].slice(0, 3).join(", ")
                                : "No samples"
                              }
                              {info.sample_values[column.name]?.length > 3 && "..."}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </CollapsibleContent>
          </Collapsible>
        ))}
      </CardContent>
    </Card>
  );
}