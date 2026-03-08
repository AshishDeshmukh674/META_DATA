'use client';

import { useState } from 'react';
import { Database, Play, Code } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Alert } from '@/components/ui/alert';
import { Loading } from '@/components/ui/loading';
import { CodeBlock } from '@/components/code-block';
import { DataTable } from '@/components/data-table';
import Navigation from '@/components/Navigation';
import toast from 'react-hot-toast';
import { executeQuery } from '@/lib/api/queries';

export default function SQLQueryPage() {
  const [storageType, setStorageType] = useState<'aws' | 'minio'>('aws');
  const [bucketName, setBucketName] = useState('metadataproject');
  const [tablePath, setTablePath] = useState('test-data/customer_data/customer_data_delta');
  const [tableFormat, setTableFormat] = useState('delta');
  const [sqlQuery, setSqlQuery] = useState('SELECT * FROM query_table LIMIT 10');
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<any>(null);

  const handleExecute = async () => {
    if (!tablePath.trim() || !sqlQuery.trim()) {
      toast.error('Please enter table path and SQL query');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await executeQuery({
        storage_type: storageType,
        bucket: bucketName,
        table_path: tablePath,
        table_format: tableFormat,
        query: sqlQuery,
      });

      setResult(response);
      toast.success('Query executed successfully!');
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to execute query';
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const sampleQueries = [
    {
      name: 'Select All',
      sql: 'SELECT * FROM query_table LIMIT 10'
    },
    {
      name: 'Count Rows',
      sql: 'SELECT COUNT(*) as total FROM query_table'
    },
    {
      name: 'Filter by ID',
      sql: "SELECT * FROM query_table WHERE CustomerID = 'C001'"
    },
    {
      name: 'Filter by City',
      sql: "SELECT * FROM query_table WHERE City = 'Mumbai'"
    },
    {
      name: 'Update Records',
      sql: "UPDATE query_table SET City = 'New Delhi' WHERE City = 'Mumbai'"
    },
    {
      name: 'Add Column',
      sql: 'ALTER TABLE query_table ADD COLUMN age INT'
    },
    {
      name: 'Delete Records',
      sql: "DELETE FROM query_table WHERE City = 'Delhi'"
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/20">
      <Navigation />

      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-3 rounded-lg bg-primary/10">
              <Code className="h-8 w-8 text-primary" />
            </div>
            <div>
              <h1 className="text-3xl font-bold">SQL Query Executor</h1>
              <p className="text-muted-foreground">Execute SQL queries directly on Delta Lake tables</p>
            </div>
          </div>
        </div>

        <div className="grid gap-6 max-w-5xl mx-auto">
          {/* Configuration Card */}
          <Card>
            <CardHeader>
              <CardTitle>Table Configuration</CardTitle>
              <CardDescription>Configure the table you want to query</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="storageType">Storage Type</Label>
                  <select
                    id="storageType"
                    value={storageType}
                    onChange={(e) => setStorageType(e.target.value as 'aws' | 'minio')}
                    className="w-full rounded-md border border-input bg-background px-3 py-2"
                  >
                    <option value="aws">AWS S3</option>
                    <option value="minio">MinIO</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="tableFormat">Table Format</Label>
                  <select
                    id="tableFormat"
                    value={tableFormat}
                    onChange={(e) => setTableFormat(e.target.value)}
                    className="w-full rounded-md border border-input bg-background px-3 py-2"
                  >
                    <option value="delta">Delta Lake</option>
                    <option value="iceberg">Apache Iceberg</option>
                    <option value="hudi">Apache Hudi</option>
                    <option value="parquet">Parquet</option>
                  </select>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="bucketName">Bucket Name</Label>
                <Input
                  id="bucketName"
                  value={bucketName}
                  onChange={(e) => setBucketName(e.target.value)}
                  placeholder="my-bucket"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="tablePath">Table Path</Label>
                <Input
                  id="tablePath"
                  value={tablePath}
                  onChange={(e) => setTablePath(e.target.value)}
                  placeholder="path/to/table"
                />
              </div>
            </CardContent>
          </Card>

          {/* SQL Editor Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-5 w-5" />
                SQL Query Editor
              </CardTitle>
              <CardDescription>
                Write your SQL query. Use 'query_table' as the table name in your SQL.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="sqlQuery">SQL Query</Label>
                <Textarea
                  id="sqlQuery"
                  value={sqlQuery}
                  onChange={(e) => setSqlQuery(e.target.value)}
                  placeholder="SELECT * FROM query_table LIMIT 10"
                  rows={8}
                  className="font-mono text-sm"
                />
              </div>

              <div className="space-y-3">
                <Label>Sample Queries</Label>
                <div className="grid grid-cols-2 gap-2">
                  {sampleQueries.map((sample, idx) => (
                    <Button
                      key={idx}
                      variant="outline"
                      size="sm"
                      onClick={() => setSqlQuery(sample.sql)}
                      className="justify-start text-left h-auto py-2"
                    >
                      <div>
                        <div className="font-medium">{sample.name}</div>
                        <div className="text-xs text-muted-foreground truncate">
                          {sample.sql}
                        </div>
                      </div>
                    </Button>
                  ))}
                </div>
              </div>

              <Button 
                onClick={handleExecute} 
                disabled={loading}
                size="lg"
                className="w-full"
              >
                {loading ? (
                  <>
                    <Loading size="sm" className="mr-2" />
                    Executing Query...
                  </>
                ) : (
                  <>
                    <Play className="mr-2 h-4 w-4" />
                    Execute Query
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Error Display */}
          {error && (
            <Alert variant="destructive">
              <p className="font-semibold">Query Failed</p>
              <p className="text-sm mt-1">{error}</p>
            </Alert>
          )}

          {/* Results Display */}
          {result && (
            <>
              {/* Query Info */}
              <Card>
                <CardHeader>
                  <CardTitle>Query Information</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="font-medium">Status:</span>
                      <span className={`ml-2 ${result.status === 'success' ? 'text-green-600' : 'text-red-600'}`}>
                        {result.status}
                      </span>
                    </div>
                    <div>
                      <span className="font-medium">Query Type:</span>
                      <span className="ml-2">{result.query_type || 'SELECT'}</span>
                    </div>
                    <div>
                      <span className="font-medium">Execution Time:</span>
                      <span className="ml-2">{result.execution_time_seconds?.toFixed(3)}s</span>
                    </div>
                    {result.rows_affected !== undefined && (
                      <div>
                        <span className="font-medium">Rows Affected:</span>
                        <span className="ml-2">{result.rows_affected}</span>
                      </div>
                    )}
                  </div>

                  {result.message && (
                    <div className="p-3 bg-muted rounded-md">
                      <p className="text-sm">{result.message}</p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Generated SQL (for NL queries) */}
              {result.generated_sql && (
                <Card>
                  <CardHeader>
                    <CardTitle>Generated SQL</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <CodeBlock
                      code={result.generated_sql}
                      language="sql"
                    />
                  </CardContent>
                </Card>
              )}

              {/* Data Results */}
              {result.query_type === 'read' && (
                <Card>
                  <CardHeader>
                    <CardTitle>Query Results</CardTitle>
                    <CardDescription>
                      {result.data && result.data.length > 0 
                        ? `Showing ${result.data.length} ${result.data.length === 1 ? 'row' : 'rows'}`
                        : 'No rows returned'
                      }
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {result.data && result.data.length > 0 ? (
                      <DataTable data={result.data} />
                    ) : (
                      <div className="p-8 text-center text-muted-foreground">
                        <p className="text-lg font-medium mb-2">No Results Found</p>
                        <p className="text-sm">
                          The query executed successfully but returned no rows.
                        </p>
                        <p className="text-sm mt-2">
                          💡 Tip: Check your WHERE conditions and make sure string values are in quotes
                        </p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}

              {/* Schema Info */}
              {result.schema && (
                <Card>
                  <CardHeader>
                    <CardTitle>Schema</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <CodeBlock
                      code={JSON.stringify(result.schema, null, 2)}
                      language="json"
                    />
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </div>
      </main>
    </div>
  );
}
