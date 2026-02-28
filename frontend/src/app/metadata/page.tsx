'use client';

import React, { useState } from 'react';
import { Navigation } from '@/components/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { LoadingCard } from '@/components/ui/loading';
import { generateMetadata } from '@/lib/api/queries';
import { TableProperties, FileText, FolderOpen, CheckCircle2, Info, Layers } from 'lucide-react';
import toast from 'react-hot-toast';

const examplePaths = [
  {
    label: 'AWS S3 CSV',
    path: 'raw/customers.csv',
    storage: 'aws' as const,
    bucket: 'my-lakehouse-bucket',
  },
  {
    label: 'MinIO CSV',
    path: 'data/customers.csv',
    storage: 'minio' as const,
    bucket: 'lakehouse',
  },
];

export default function MetadataPage() {
  const [csvPath, setCsvPath] = useState('raw/customers.csv');
  const [storageType, setStorageType] = useState('aws');
  const [bucketName, setBucketName] = useState('my-lakehouse-bucket');
  const [forceRefresh, setForceRefresh] = useState(false);
  
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');

  const handleLoadExample = (example: typeof examplePaths[0]) => {
    setCsvPath(example.path);
    setStorageType(example.storage);
    setBucketName(example.bucket);
    toast.success('Example loaded!');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!csvPath.trim()) {
      toast.error('Please enter a CSV file path');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await generateMetadata({
        storage_type: storageType as 'aws' | 'minio',
        bucket: bucketName,
        path: csvPath,
        table_format: 'delta',
        force_refresh: forceRefresh,
      });

      setResult(response);
      toast.success(`Metadata generated successfully! ${response.snapshot_id} created`);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Metadata generation failed';
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
            <div className="h-12 w-12 rounded-lg bg-gradient-to-br from-green-500 to-emerald-500 flex items-center justify-center">
              <TableProperties className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold">Metadata Generation</h1>
              <p className="text-muted-foreground">Convert CSV files to Delta Lake format.</p>
            </div>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Left: Form & Results */}
          <div className="lg:col-span-2 space-y-6">
            {/* Examples */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Example Paths</CardTitle>
                <CardDescription>Click to load an example configuration</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-3">
                  {examplePaths.map((example, index) => (
                    <Button
                      key={index}
                      variant="outline"
                      onClick={() => handleLoadExample(example)}
                      className="flex-col h-auto py-3"
                    >
                      <div className="font-medium mb-1">{example.label}</div>
                      <div className="text-xs text-muted-foreground font-mono">{example.path}</div>
                    </Button>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Form */}
            <Card>
              <CardHeader>
                <CardTitle>CSV Configuration</CardTitle>
                <CardDescription>Specify your CSV file details</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="csvPath">
                      <FileText className="inline h-4 w-4 mr-1" />
                      CSV File Path
                    </Label>
                    <Input
                      id="csvPath"
                      value={csvPath}
                      onChange={(e) => setCsvPath(e.target.value)}
                      placeholder="raw/customers.csv"
                      className="font-mono text-sm"
                    />
                    <p className="text-xs text-muted-foreground">
                      Path to your CSV file relative to S3 bucket
                    </p>
                  </div>

                  <div className="grid md:grid-cols-2 gap-4">
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
                      <Label htmlFor="bucketName">
                        <FolderOpen className="inline h-4 w-4 mr-1" />
                        S3 Bucket Name
                      </Label>
                      <Input
                        id="bucketName"
                        value={bucketName}
                        onChange={(e) => setBucketName(e.target.value)}
                        placeholder="my-lakehouse-bucket"
                      />
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="forceRefresh"
                      checked={forceRefresh}
                      onChange={(e) => setForceRefresh(e.target.checked)}
                      className="h-4 w-4 rounded border-gray-300"
                    />
                    <Label htmlFor="forceRefresh" className="cursor-pointer">
                      Force Refresh (regenerate metadata even if it exists)
                    </Label>
                  </div>

                  <Button 
                    type="submit" 
                    className="w-full"
                    disabled={loading || !csvPath.trim()}
                  >
                    {loading ? 'Generating...' : 'Generate Metadata'}
                  </Button>
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

            {/* Loading State */}
            {loading && <LoadingCard message="Converting CSV to Delta Lake..." />}

            {/* Success Result */}
            {result && (
              <Alert variant="success">
                <CheckCircle2 className="h-4 w-4" />
                <AlertTitle>Metadata Generated Successfully!</AlertTitle>
                <AlertDescription>
                  <div className="mt-3 space-y-2 text-sm">
                    <div className="grid grid-cols-2 gap-2">
                      <div className="font-medium">Snapshot ID:</div>
                      <div className="font-mono">{result.snapshot_id}</div>
                      
                      <div className="font-medium">Table Location:</div>
                      <div className="font-mono text-xs break-all">{result.table_location}</div>
                      
                      <div className="font-medium">Delta Path:</div>
                      <div className="font-mono text-xs break-all">{result.delta_path}</div>
                      
                      {result.row_count !== undefined && (
                        <>
                          <div className="font-medium">Row Count:</div>
                          <div>{result.row_count.toLocaleString()}</div>
                        </>
                      )}
                      
                      {result.columns && (
                        <>
                          <div className="font-medium">Columns:</div>
                          <div>{result.columns.length}</div>
                        </>
                      )}
                    </div>
                  </div>
                </AlertDescription>
              </Alert>
            )}

            {/* Schema Display */}
            {result && result.schema && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Detected Schema</CardTitle>
                  <CardDescription>
                    {result.schema.length} columns detected from CSV
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {result.schema.map((col: any, index: number) => (
                      <div
                        key={index}
                        className="flex items-center justify-between p-3 bg-muted rounded-lg"
                      >
                        <div className="flex items-center gap-3">
                          <div className="h-8 w-8 rounded bg-primary/10 text-primary flex items-center justify-center text-xs font-bold">
                            {index + 1}
                          </div>
                          <div>
                            <div className="font-mono font-medium">{col.name}</div>
                            {col.nullable !== undefined && (
                              <div className="text-xs text-muted-foreground">
                                {col.nullable ? 'Nullable' : 'Required'}
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="text-sm font-mono text-blue-600 dark:text-blue-400">
                          {col.type}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Right: Info & Process */}
          <div className="space-y-6">
            {/* Process Flow */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Layers className="h-5 w-5 text-green-500" />
                  Conversion Process
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-start gap-2">
                  <div className="h-6 w-6 rounded-full bg-green-100 text-green-600 flex items-center justify-center flex-shrink-0 text-xs font-bold">1</div>
                  <div>
                    <div className="font-medium text-sm">Read CSV</div>
                    <div className="text-xs text-muted-foreground">Load and parse your CSV file</div>
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <div className="h-6 w-6 rounded-full bg-green-100 text-green-600 flex items-center justify-center flex-shrink-0 text-xs font-bold">2</div>
                  <div>
                    <div className="font-medium text-sm">Detect Schema</div>
                    <div className="text-xs text-muted-foreground">Automatically infer column types</div>
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <div className="h-6 w-6 rounded-full bg-green-100 text-green-600 flex items-center justify-center flex-shrink-0 text-xs font-bold">3</div>
                  <div>
                    <div className="font-medium text-sm">Convert Format</div>
                    <div className="text-xs text-muted-foreground">Write to Delta Lake format</div>
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <div className="h-6 w-6 rounded-full bg-green-100 text-green-600 flex items-center justify-center flex-shrink-0 text-xs font-bold">4</div>
                  <div>
                    <div className="font-medium text-sm">Create Snapshot</div>
                    <div className="text-xs text-muted-foreground">Generate version metadata</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Info & Tips */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Info className="h-5 w-5 text-blue-500" />
                  Important Notes
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div>
                  <div className="font-medium mb-1">📁 File Format</div>
                  <div className="text-muted-foreground">
                    Only CSV files are supported. Ensure proper formatting with headers.
                  </div>
                </div>
                <div>
                  <div className="font-medium mb-1">🔄 Force Refresh</div>
                  <div className="text-muted-foreground">
                    Enable to regenerate metadata even if Delta table already exists.
                  </div>
                </div>
                <div>
                  <div className="font-medium mb-1">💾 Storage Location</div>
                  <div className="text-muted-foreground">
                    Delta files are stored in: <span className="font-mono">data/delta/[table_name]</span>
                  </div>
                </div>
                <div>
                  <div className="font-medium mb-1">⚡ Performance</div>
                  <div className="text-muted-foreground">
                    Conversion time depends on CSV size. Small files: ~1-2 seconds.
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Benefits */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Delta Lake Benefits</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <div className="flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                  <span>ACID transactions for data reliability</span>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                  <span>Time travel to query historical versions</span>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                  <span>Schema evolution support</span>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                  <span>Better compression than CSV</span>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                  <span>Fast columnar queries with Parquet</span>
                </div>
              </CardContent>
            </Card>

            {/* Next Steps */}
            <Alert variant="info">
              <AlertTitle>After Generation</AlertTitle>
              <AlertDescription className="text-sm mt-2 space-y-1">
                <div>1. Note your snapshot ID</div>
                <div>2. Use the table path in SQL or Natural Language queries</div>
                <div>3. View snapshots in the Snapshots page</div>
              </AlertDescription>
            </Alert>
          </div>
        </div>
      </main>
    </div>
  );
}
