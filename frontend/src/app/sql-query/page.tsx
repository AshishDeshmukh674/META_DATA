'use client';

import React, { useState } from 'react';
import { Navigation } from '@/components/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { LoadingCard } from '@/components/ui/loading';
import { DataTable } from '@/components/data-table';
import { CodeBlock } from '@/components/code-block';
import { executeSQL, checkHealth } from '@/lib/api/queries';
import { Database, Play, Zap, Info, Activity } from 'lucide-react';
import toast from 'react-hot-toast';

const exampleQueries = [
  {
    name: 'Select All',
    sql: 'SELECT * FROM delta.default.customers LIMIT 10;',
    description: 'Fetch first 10 rows from customers table',
  },
  {
    name: 'Count by City',
    sql: 'SELECT city, COUNT(*) as count\nFROM delta.default.customers\nGROUP BY city\nORDER BY count DESC;',
    description: 'Count customers grouped by city',
  },
  {
    name: 'Filter by Email',
    sql: "SELECT name, email, city\nFROM delta.default.customers\nWHERE email LIKE '%gmail.com'\nLIMIT 20;",
    description: 'Find customers with Gmail addresses',
  },
  {
    name: 'Age Statistics',
    sql: 'SELECT \n  MIN(age) as min_age,\n  MAX(age) as max_age,\n  AVG(age) as avg_age,\n  COUNT(*) as total\nFROM delta.default.customers;',
    description: 'Calculate age statistics',
  },
  {
    name: 'Top Cities',
    sql: 'SELECT city, COUNT(*) as customer_count\nFROM delta.default.customers\nGROUP BY city\nHAVING COUNT(*) > 5\nORDER BY customer_count DESC;',
    description: 'Cities with more than 5 customers',
  },
];

export default function SQLQueryPage() {
  const [sqlQuery, setSqlQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState('');
  const [connectionStatus, setConnectionStatus] = useState<'unknown' | 'checking' | 'connected' | 'failed'>('unknown');

  const handleLoadExample = (sql: string) => {
    setSqlQuery(sql);
    toast.success('Example loaded! Click "Execute" to run it.');
  };

  const handleCheckConnection = async () => {
    setConnectionStatus('checking');
    
    try {
      await checkHealth();
      setConnectionStatus('connected');
      toast.success('Connection successful!');
    } catch (err: any) {
      setConnectionStatus('failed');
      toast.error('Connection failed. Is the server running?');
    }
  };

  const handleExecute = async () => {
    if (!sqlQuery.trim()) {
      toast.error('Please enter a SQL query');
      return;
    }

    setLoading(true);
    setError('');
    setResults(null);

    try {
      const response = await executeSQL(sqlQuery);
      setResults(response);
      toast.success(`Query executed! ${response.row_count} rows returned in ${response.execution_time_ms}ms`);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Query execution failed';
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Execute on Ctrl+Enter
    if (e.ctrlKey && e.key === 'Enter') {
      e.preventDefault();
      handleExecute();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/20">
      <Navigation />
      
      <main className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-3">
            <div className="h-12 w-12 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
              <Database className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold">SQL Query Editor</h1>
              <p className="text-muted-foreground">Execute SQL queries directly on Trino.</p>
            </div>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Left: Query Editor */}
          <div className="lg:col-span-2 space-y-6">
            {/* Query Editor */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>SQL Editor</CardTitle>
                    <CardDescription>Write and execute SQL queries (Ctrl+Enter to run)</CardDescription>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleCheckConnection}
                    disabled={connectionStatus === 'checking'}
                  >
                    <Activity className={`mr-2 h-4 w-4 ${connectionStatus === 'connected' ? 'text-green-500' : connectionStatus === 'failed' ? 'text-red-500' : ''}`} />
                    {connectionStatus === 'checking' ? 'Checking...' : 'Test Connection'}
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <Textarea
                    value={sqlQuery}
                    onChange={(e) => setSqlQuery(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Enter your SQL query here...&#10;&#10;Example:&#10;SELECT * FROM delta.default.customers LIMIT 10;"
                    className="font-mono text-sm min-h-[200px]"
                  />
                  <div className="flex gap-3">
                    <Button 
                      onClick={handleExecute}
                      disabled={loading || !sqlQuery.trim()}
                      className="flex-1"
                    >
                      <Play className="mr-2 h-4 w-4" />
                      {loading ? 'Executing...' : 'Execute Query'}
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => {
                        setSqlQuery('');
                        setResults(null);
                        setError('');
                      }}
                    >
                      Clear
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Error Display */}
            {error && (
              <Alert variant="destructive">
                <AlertTitle>Query Error</AlertTitle>
                <AlertDescription>
                  <div className="font-mono text-sm mt-2">{error}</div>
                </AlertDescription>
              </Alert>
            )}

            {/* Loading State */}
            {loading && <LoadingCard message="Executing SQL query..." />}

            {/* Results */}
            {results && results.data && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Zap className="h-5 w-5 text-yellow-500" />
                    Query Results
                  </CardTitle>
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

            {/* Query Formatted */}
            {sqlQuery && !loading && !results && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Query Preview</CardTitle>
                </CardHeader>
                <CardContent>
                  <CodeBlock code={sqlQuery} language="sql" />
                </CardContent>
              </Card>
            )}
          </div>

          {/* Right: Examples & Tips */}
          <div className="space-y-6">
            {/* Example Queries */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Example Queries</CardTitle>
                <CardDescription>Click to load and try</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {exampleQueries.map((example, index) => (
                  <div
                    key={index}
                    className="p-3 border rounded-lg hover:bg-muted/50 cursor-pointer transition-colors"
                    onClick={() => handleLoadExample(example.sql)}
                  >
                    <div className="font-medium text-sm mb-1">{example.name}</div>
                    <div className="text-xs text-muted-foreground mb-2">{example.description}</div>
                    <div className="font-mono text-xs bg-muted p-2 rounded overflow-x-auto">
                      {example.sql.split('\n')[0]}...
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Tips Card */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Info className="h-5 w-5 text-blue-500" />
                  SQL Tips
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div>
                  <div className="font-medium mb-1">📝 Table Format</div>
                  <div className="text-muted-foreground font-mono text-xs">
                    delta.default.table_name
                  </div>
                </div>
                <div>
                  <div className="font-medium mb-1">⚡ Fast Execution</div>
                  <div className="text-muted-foreground">
                    Queries typically complete in 100-500ms
                  </div>
                </div>
                <div>
                  <div className="font-medium mb-1">🔍 Use LIMIT</div>
                  <div className="text-muted-foreground">
                    Add LIMIT to large queries to avoid timeouts
                  </div>
                </div>
                <div>
                  <div className="font-medium mb-1">⌨️ Keyboard Shortcut</div>
                  <div className="text-muted-foreground">
                    Press <kbd className="px-1.5 py-0.5 bg-muted rounded text-xs">Ctrl+Enter</kbd> to execute
                  </div>
                </div>
                <div>
                  <div className="font-medium mb-1">📊 Supported Functions</div>
                  <div className="text-muted-foreground">
                    COUNT, SUM, AVG, MIN, MAX, GROUP BY, ORDER BY, JOIN
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Trino Info */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">About Trino</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm text-muted-foreground">
                <p>
                  Trino is a distributed SQL query engine designed for fast analytic queries against data of any size.
                </p>
                <p>
                  It reads data directly from Delta Lake using the Delta connector, providing low-latency queries without a metastore.
                </p>
                <div className="pt-2 space-y-1">
                  <div className="flex items-center gap-2">
                    <Zap className="h-3 w-3 text-yellow-500" />
                    <span>Lightning fast execution</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Database className="h-3 w-3 text-blue-500" />
                    <span>Direct Delta Lake access</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Activity className="h-3 w-3 text-green-500" />
                    <span>Running on port 8080</span>
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
