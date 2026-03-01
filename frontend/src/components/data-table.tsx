'use client';

interface DataTableProps {
  data: any[];
  columns?: string[];
}

export function DataTable({ data, columns }: DataTableProps) {
  if (!data || data.length === 0) {
    return <div className="text-center py-8 text-muted-foreground">No data to display</div>;
  }

  const tableColumns = columns || Object.keys(data[0]);

  return (
    <div className="overflow-auto rounded-lg border">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b bg-muted/50">
            {tableColumns.map((column) => (
              <th key={column} className="px-4 py-3 text-left font-medium">
                {column}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, idx) => (
            <tr key={idx} className="border-b last:border-0 hover:bg-muted/30">
              {tableColumns.map((column) => (
                <td key={column} className="px-4 py-3">
                  {typeof row[column] === 'object'
                    ? JSON.stringify(row[column])
                    : String(row[column] ?? '')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
