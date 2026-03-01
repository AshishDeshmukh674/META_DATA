'use client';

import { useState } from 'react';
import { MessageSquare, Sparkles, Database } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert } from '@/components/ui/alert';
import { Loading } from '@/components/ui/loading';
import { CodeBlock } from '@/components/code-block';
import { DataTable } from '@/components/data-table';
import Navigation from '@/components/Navigation';
import toast from 'react-hot-toast';
import { executeNLQuery } from '@/lib/api/queries';

export default function NaturalLanguagePage() {
  const [storageType, setStorageType] = useState<'aws' | 'minio'>('aws');
  const [bucketName, setBucketName] = useState('metadataproject');
  const [tablePath, setTablePath] = useState('test-data/customer_data/customer_data_delta');
  const [tableFormat, setTableFormat] = useState('delta');
  const [question, setQuestion] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<any>(null);

  const handleQuery = async () => {
    if (!tablePath.trim() || !question.trim()) {
      toast.error('Please enter table path and your question');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await executeNLQuery({
        storage_type: storageType,
        bucket: bucketName,
        table_path: tablePath,
        question: question,
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

  const sampleQuestions = [
    'Show me the top 10 customers by total purchases',
    'What is the average order value?',
    'How many orders were placed last month?',
    'Show me all customers from California',
    'What are the most popular products?',
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/20">
      <Navigation />

      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-3 rounded-lg bg-primary/10">
              <MessageSquare className="h-8 w-8 text-primary" />
            </div>
            <div>
              <h1 className="text-3xl font-bold">Natural Language Queries</h1>
              <p className="text-muted-foreground">Ask questions about your data in plain English</p>
            </div>
          </div>
        </div>

        <div className="grid gap-6 max-w-4xl mx-auto">
          {/* Configuration Card */}
          <Card>
            <CardHeader>
              <CardTitle>Table Configuration</CardTitle>
              <CardDescription>Select the table you want to query</CardDescription>
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
                  <Label htmlFor="bucketName">Bucket Name</Label>
                  <Input
                    id="bucketName"
                    value={bucketName}
                    onChange={(e) => setBucketName(e.target.value)}
                    placeholder="my-bucket"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="tableFormat">Table Format</Label>
                <select
                  id="tableFormat"
                  value={tableFormat}
                  onChange={(e) => setTableFormat(e.target.value)}
                  className="w-full rounded-md border border-input bg-background px-3 py-2"
                >
                  <option value="">Auto-detect</option>
                  <option value="delta">Delta Lake</option>
                  <option value="iceberg">Apache Iceberg</option>
                  <option value="hudi">Apache Hudi</option>
                  <option value="parquet">Parquet</option>
                </select>
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

          {/* Query Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5" />
                Ask Your Question
              </CardTitle>
              <CardDescription>
                Write your question in plain English - AI will convert it to SQL
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Alert>
                <p className="text-sm">
                  <strong>Natural Language Query:</strong> Ask questions about your data in plain English.
                  The AI will generate appropriate SQL queries and execute them against your table.
                </p>
              </Alert>

              <div className="space-y-2">
                <Label htmlFor="question">Your Question</Label>
                <textarea
                  id="question"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="e.g., Show me the top 10 customers by revenue"
                  className="w-full min-h-[100px] rounded-md border border-input bg-background px-3 py-2"
                />
              </div>

              {/* Sample Questions */}
              <div className="space-y-2">
                <Label className="text-sm text-muted-foreground">Sample Questions:</Label>
                <div className="flex flex-wrap gap-2">
                  {sampleQuestions.map((q, idx) => (
                    <button
                      key={idx}
                      onClick={() => setQuestion(q)}
                      className="text-xs px-3 py-1 rounded-full bg-muted hover:bg-muted/80 transition-colors"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>

              <Button onClick={handleQuery} disabled={loading} className="w-full">
                {loading ? <Loading size="sm" /> : (
                  <>
                    <Database className="h-4 w-4 mr-2" />
                    Execute Query
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Error Display */}
          {error && (
            <Alert variant="destructive">
              <p className="text-sm font-medium">Error</p>
              <p className="text-sm">{error}</p>
            </Alert>
          )}

          {/* Results Display */}
          {result && (
            <>
              {/* Generated SQL */}
              {result.generated_sql && (
                <Card>
                  <CardHeader>
                    <CardTitle>Generated SQL</CardTitle>
                    <CardDescription>The AI-generated query for your question</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <CodeBlock code={result.generated_sql} language="sql" />
                  </CardContent>
                </Card>
              )}

              {/* Query Results */}
              {result.data && result.data.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Results ({result.row_count} rows)</CardTitle>
                    <CardDescription>{result.explanation || 'Query results'}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <DataTable data={result.data} columns={result.columns || []} />
                  </CardContent>
                </Card>
              )}

              {/* Full Response */}
              <Card>
                <CardHeader>
                  <CardTitle>Full Response</CardTitle>
                </CardHeader>
                <CardContent>
                  <CodeBlock code={JSON.stringify(result, null, 2)} language="json" />
                </CardContent>
              </Card>
            </>
          )}
        </div>
      </main>
    </div>
  );
}
