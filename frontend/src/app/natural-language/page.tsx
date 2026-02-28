'use client';

import React, { useState } from 'react';
import { Navigation } from '@/components/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { LoadingCard } from '@/components/ui/loading';
import { DataTable } from '@/components/data-table';
import { CodeBlock } from '@/components/code-block';
import { executeNaturalLanguageQuery, syncTable, getTableInfo } from '@/lib/api/queries';
import { MessageSquare, Sparkles, Database, Info, ArrowRight } from 'lucide-react';
import toast from 'react-hot-toast';

const exampleQueries = [
  'Show me all customers from Mumbai',
  'Count the number of customers in each city',
  'Find all customers with gmail addresses',
  'List customers sorted by age',
  'Show me the first 10 customers',
  'Get distinct cities from customers',
];

export default function NaturalLanguagePage() {
  const [query, setQuery] = useState('');
  const [storageType, setStorageType] = useState('aws');
  const [bucketName, setBucketName] = useState('my-lakehouse-bucket');
  const [tablePath, setTablePath] = useState('delta/customers');
  
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [generatedSQL, setGeneratedSQL] = useState('');
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState('');
  const [tableInfo, setTableInfo] = useState<any>(null);

  const handleLoadExample = (example: string) => {
    setQuery(example);
    toast.success('Example loaded! Click "Ask Question" to run it.');
  };

  const handleSyncTable = async () => {
    if (!tablePath.trim()) {
      toast.error('Please enter a table path');
      return;
    }

    setSyncing(true);
    setError('');
    
    try {
      const response = await syncTable(
        storageType as 'aws' | 'minio',
        bucketName,
        tablePath
      );
      
      toast.success(`Table synced successfully! ${response.message}`);
      setTableInfo(response);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to sync table';
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setSyncing(false);
    }
  };

  const handleGetTableInfo = async () => {
    if (!tablePath.trim()) {
      toast.error('Please enter a table path');
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      const info = await getTableInfo(
        'delta',
        'default',
        tablePath.split('/').pop() || 'customers'
      );
      
      setTableInfo(info);
      toast.success('Table info loaded');
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to get table info';
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!query.trim()) {
      toast.error('Please enter a question');
      return;
    }

    if (!tablePath.trim()) {
      toast.error('Please enter a table path');
      return;
    }

    setLoading(true);
    setError('');
    setResults(null);
    setGeneratedSQL('');

    try {
      const response = await executeNaturalLanguageQuery({
        query: query,
        storage_type: storageType as 'aws' | 'minio',
        bucket: bucketName,
        table_path: tablePath,
      });

      setGeneratedSQL(response.sql);
      setResults(response);
      toast.success(`Query executed successfully! ${response.row_count} rows returned`);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Query execution failed';
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/20">
      <Navigation />
      
      <main className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-3">
            <div className="h-12 w-12 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
              <MessageSquare className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold">Natural Language Query</h1>
              <p className="text-muted-foreground">Ask questions in plain English. AI converts them to SQL.</p>
            </div>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Left: Query Form */}
          <div className="lg:col-span-2 space-y-6">
            {/* Example Queries */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-yellow-500" />
                  Example Questions
                </CardTitle>
                <CardDescription>Click any example to try it out</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {exampleQueries.map((example, index) => (
                    <Button
                      key={index}
                      variant="outline"
                      size="sm"
                      onClick={() => handleLoadExample(example)}
                      className="text-left justify-start"
                    >
                      {example}
                    </Button>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Query Input Form */}
            <Card>
              <CardHeader>
                <CardTitle>Your Question</CardTitle>
                <CardDescription>Ask anything about your data</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="query">Natural Language Query</Label>
                    <Input
                      id="query"
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      placeholder="e.g., Show me all customers from Mumbai"
                      className="text-base"
                    />
                  </div>

                  <div className="grid md:grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="storageType">Storage Type</Label>
                      <select
                        id="storageType"
                        value={storageType}
                        onChange={(e) => setStorageType(e.target.value)}
                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                      >
                        <option value="aws">AWS S3</option>
                        <option value="minio">MinIO</option>
                      </select>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="bucketName">S3 Bucket Name</Label>
                        <Input
                          id="bucketName"
                          value={bucketName}
                          onChange={(e) => setBucketName(e.target.value)}
                          placeholder="my-lakehouse-bucket"
                        />
                      </div>

                    <div className="space-y-2">
                      <Label htmlFor="tablePath">Table Path</Label>
                      <Input
                        id="tablePath"
                        value={tablePath}
                        onChange={(e) => setTablePath(e.target.value)}
                        placeholder="C:/path/to/delta/table or delta/table"
                      />
                    </div>
                  </div>

                  <div className="flex gap-3">
                    <Button 
                      type="submit" 
                      className="flex-1"
                      disabled={loading || !query.trim() || !tablePath.trim()}
                    >
                      {loading ? 'Processing...' : 'Ask Question'}
                      <ArrowRight className="ml-2 h-4 w-4" />
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      onClick={handleSyncTable}
                      disabled={syncing || !tablePath.trim()}
                    >
                      <Database className="mr-2 h-4 w-4" />
                      {syncing ? 'Syncing...' : 'Sync Table'}
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>

            {/* Error Display */}
            {error && (
              <Alert variant="destructive">
                <AlertTitle>Error</AlertTitle>
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {/* Generated SQL */}
            {generatedSQL && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Generated SQL</CardTitle>
                  <CardDescription>AI-generated SQL query from your question</CardDescription>
                </CardHeader>
                <CardContent>
                  <CodeBlock code={generatedSQL} language="sql" />
                </CardContent>
              </Card>
            )}

            {/* Loading State */}
            {loading && <LoadingCard message="Processing your question..." />}

            {/* Results */}
            {results && results.data && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Query Results</CardTitle>
                  <CardDescription>
                    {results.row_count} rows returned in {results.execution_time_ms}ms
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <DataTable 
                    data={results.data} 
                    columns={results.columns}
                    rowCount={results.row_count}
                    executionTime={results.execution_time_ms}
                  />
                </CardContent>
              </Card>
            )}
          </div>

          {/* Right: Info & Tips */}
          <div className="space-y-6">
            {/* Table Info */}
            {tableInfo && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Table Information</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div>
                    <div className="text-sm font-medium text-muted-foreground">Table Name</div>
                    <div className="text-sm font-mono">{tableInfo.table_name || 'N/A'}</div>
                  </div>
                  <div>
                    <div className="text-sm font-medium text-muted-foreground">Columns</div>
                    <div className="text-sm">
                      {tableInfo.columns?.length || tableInfo.schema?.length || 'Unknown'}
                    </div>
                  </div>
                  {tableInfo.schema && (
                    <div>
                      <div className="text-sm font-medium text-muted-foreground mb-1">Schema</div>
                      <div className="space-y-1">
                        {tableInfo.schema.map((col: any, idx: number) => (
                          <div key={idx} className="text-xs font-mono bg-muted p-2 rounded">
                            {col.name}: <span className="text-blue-600">{col.type}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Tips Card */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Info className="h-5 w-5 text-blue-500" />
                  Tips & Best Practices
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div>
                  <div className="font-medium mb-1">🎯 Be Specific</div>
                  <div className="text-muted-foreground">
                    "Show customers from Mumbai" is better than "Show customers"
                  </div>
                </div>
                <div>
                  <div className="font-medium mb-1">📊 Use Aggregations</div>
                  <div className="text-muted-foreground">
                    Try "Count", "Sum", "Average", "Group by" in your questions
                  </div>
                </div>
                <div>
                  <div className="font-medium mb-1">🔄 Sync First</div>
                  <div className="text-muted-foreground">
                    Click "Sync Table" before your first query to register the schema
                  </div>
                </div>
                <div>
                  <div className="font-medium mb-1">⚡ Performance</div>
                  <div className="text-muted-foreground">
                    Natural language queries take ~1-2 seconds (LLM processing)
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* How it Works */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">How It Works</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <div className="flex items-start gap-2">
                  <div className="h-6 w-6 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center flex-shrink-0 text-xs font-bold">1</div>
                  <div>
                    <div className="font-medium">AI Conversion</div>
                    <div className="text-muted-foreground">Your question is sent to Groq LLM</div>
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <div className="h-6 w-6 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center flex-shrink-0 text-xs font-bold">2</div>
                  <div>
                    <div className="font-medium">SQL Generation</div>
                    <div className="text-muted-foreground">AI generates optimized SQL query</div>
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <div className="h-6 w-6 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center flex-shrink-0 text-xs font-bold">3</div>
                  <div>
                    <div className="font-medium">Query Execution</div>
                    <div className="text-muted-foreground">Trino executes the query on Delta Lake</div>
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <div className="h-6 w-6 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center flex-shrink-0 text-xs font-bold">4</div>
                  <div>
                    <div className="font-medium">Results</div>
                    <div className="text-muted-foreground">Data returned and displayed beautifully</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
