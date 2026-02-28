'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { formatDuration } from '@/lib/utils';
import { Table, Database, Clock } from 'lucide-react';

interface DataTableProps {
  data: Record<string, any>[];
  columns: string[];
  rowCount?: number;
  executionTime?: number;
  title?: string;
}

export function DataTable({ 
  data, 
  columns, 
  rowCount, 
  executionTime,
  title = 'Query Results'
}: DataTableProps) {
  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
            <Database className="h-12 w-12 mb-4 opacity-50" />
            <p>No data to display</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Table className="h-5 w-5" />
            {title}
          </CardTitle>
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            {rowCount !== undefined && (
              <span className="flex items-center gap-1">
                <Database className="h-4 w-4" />
                {rowCount} rows
              </span>
            )}
            {executionTime !== undefined && (
              <span className="flex items-center gap-1">
                <Clock className="h-4 w-4" />
                {formatDuration(executionTime)}
              </span>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border overflow-hidden">
          <div className="overflow-x-auto max-h-[600px] overflow-y-auto">
            <table className="w-full">
              <thead className="bg-muted/50 sticky top-0 z-10">
                <tr>
                  {columns.map((column) => (
                    <th
                      key={column}
                      className="px-4 py-3 text-left text-sm font-semibold text-foreground border-b"
                    >
                      {column}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.map((row, rowIndex) => (
                  <tr
                    key={rowIndex}
                    className="border-b hover:bg-muted/30 transition-colors"
                  >
                    {columns.map((column) => (
                      <td
                        key={column}
                        className="px-4 py-3 text-sm text-muted-foreground"
                      >
                        {row[column] !== null && row[column] !== undefined
                          ? String(row[column])
                          : <span className="text-muted-foreground/50">null</span>}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
