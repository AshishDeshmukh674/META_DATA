'use client';

import React, { useState, useEffect } from 'react';
import { Navigation } from '@/components/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { LoadingCard, LoadingSpinner } from '@/components/ui/loading';
import { DataTable } from '@/components/data-table';
import { listSnapshots, executeSQL } from '@/lib/api/queries';
import { Layers, Clock, Database, Search, Calendar, Hash } from 'lucide-react';
import { formatTimestamp } from '@/lib/utils';
import toast from 'react-hot-toast';

export default function SnapshotsPage() {
  const [storageType, setStorageType] = useState('aws');
  const [bucketName, setBucketName] = useState('my-lakehouse-bucket');
  const [tablePath, setTablePath] = useState('delta/customers');
  
  const [loadingSnapshots, setLoadingSnapshots] = useState(false);
  const [snapshots, setSnapshots] = useState<any[]>([]);
  const [selectedSnapshot, setSelectedSnapshot] = useState<any>(null);
  
  const [queryLoading, setQueryLoading] = useState(false);
  const [queryResults, setQueryResults] = useState<any>(null);
  const [error, setError] = useState('');

  const handleLoadSnapshots = async () => {
    if (!tablePath.trim()) {
      toast.error('Please enter a table path');
      return;
    }

    setLoadingSnapshots(true);
    setError('');
    setSnapshots([]);
    setSelectedSnapshot(null);

    try {
      const response = await listSnapshots(
        storageType as 'aws' | 'minio',
        bucketName,
        tablePath
      );

      setSnapshots(response.snapshots || []);
      toast.success(`Loaded ${response.snapshots?.length || 0} snapshots`);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to load snapshots';
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setLoadingSnapshots(false);
    }
  };

  const handleQuerySnapshot = async (snapshotId: number) => {
    setQueryLoading(true);
    setError('');
    setQueryResults(null);

    try {
      // Build query with snapshot ID
      const query = `SELECT * FROM delta.default.customers FOR VERSION AS OF ${snapshotId} LIMIT 50`;
      
      const response = await executeSQL(query);
      setQueryResults(response);
      setSelectedSnapshot(snapshots.find(s => s.snapshot_id === snapshotId));
      toast.success(`Queried snapshot ${snapshotId}: ${response.row_count} rows`);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Query failed';
      toast.error(errorMsg);
    } finally {
      setQueryLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/20">
      <Navigation />
      
      <main className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-3">
            <div className="h-12 w-12 rounded-lg bg-gradient-to-br from-orange-500 to-red-500 flex items-center justify-center">
              <Layers className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold">Snapshots & Time Travel</h1>
              <p className="text-muted-foreground">Query historical versions of your data.</p>
            </div>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Left: Snapshots List */}
          <div className="lg:col-span-2 space-y-6">
            {/* Load Snapshots Form */}
            <Card>
              <CardHeader>
                <CardTitle>Table Configuration</CardTitle>
                <CardDescription>Specify the Delta table to view snapshots</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
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
                      <Label htmlFor="tablePath">Delta Table Path</Label>
                      <Input
                        id="tablePath"
                        value={tablePath}
                        onChange={(e) => setTablePath(e.target.value)}
                        placeholder="delta/customers"
                      />
                    </div>
                  </div>

                  <Button 
                    onClick={handleLoadSnapshots}
                    disabled={loadingSnapshots || !tablePath.trim()}
                    className="w-full"
                  >
                    {loadingSnapshots ? (
                      <>
                        <LoadingSpinner size="sm" className="mr-2" />
                        Loading...
                      </>
                    ) : (
                      <>
                        <Search className="mr-2 h-4 w-4" />
                        Load Snapshots
                      </>
                    )}
                  </Button>
                </div>
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
            {loadingSnapshots && <LoadingCard message="Loading snapshot history..." />}

            {/* Snapshots List */}
            {snapshots.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Available Snapshots</CardTitle>
                  <CardDescription>
                    {snapshots.length} version{snapshots.length !== 1 ? 's' : ''} found
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {snapshots.map((snapshot, index) => (
                      <div
                        key={snapshot.snapshot_id || index}
                        className={`p-4 border rounded-lg transition-all ${
                          selectedSnapshot?.snapshot_id === snapshot.snapshot_id
                            ? 'border-primary bg-primary/5'
                            : 'hover:bg-muted/50'
                        }`}
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center gap-3">
                            <div className="h-10 w-10 rounded-full bg-orange-100 text-orange-600 flex items-center justify-center font-bold">
                              {snapshot.snapshot_id || index + 1}
                            </div>
                            <div>
                              <div className="font-medium flex items-center gap-2">
                                <Hash className="h-4 w-4" />
                                Snapshot {snapshot.snapshot_id}
                              </div>
                              {snapshot.timestamp && (
                                <div className="text-sm text-muted-foreground flex items-center gap-1">
                                  <Clock className="h-3 w-3" />
                                  {formatTimestamp(snapshot.timestamp)}
                                </div>
                              )}
                            </div>
                          </div>
                          <Button
                            size="sm"
                            onClick={() => handleQuerySnapshot(snapshot.snapshot_id)}
                            disabled={queryLoading}
                          >
                            <Database className="mr-2 h-3 w-3" />
                            Query
                          </Button>
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                          {snapshot.operation && (
                            <div>
                              <div className="text-muted-foreground text-xs">Operation</div>
                              <div className="font-medium">{snapshot.operation}</div>
                            </div>
                          )}
                          {snapshot.row_count !== undefined && (
                            <div>
                              <div className="text-muted-foreground text-xs">Rows</div>
                              <div className="font-medium">{snapshot.row_count.toLocaleString()}</div>
                            </div>
                          )}
                          {snapshot.file_count !== undefined && (
                            <div>
                              <div className="text-muted-foreground text-xs">Files</div>
                              <div className="font-medium">{snapshot.file_count}</div>
                            </div>
                          )}
                          {snapshot.size_bytes !== undefined && (
                            <div>
                              <div className="text-muted-foreground text-xs">Size</div>
                              <div className="font-medium">
                                {(snapshot.size_bytes / 1024 / 1024).toFixed(2)} MB
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Query Results */}
            {queryLoading && <LoadingCard message="Querying snapshot..." />}

            {queryResults && queryResults.data && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Snapshot Data</CardTitle>
                  <CardDescription>
                    Snapshot {selectedSnapshot?.snapshot_id} - {queryResults.row_count} rows (showing first 50)
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <DataTable 
                    data={queryResults.data}
                    columns={queryResults.columns}
                    rowCount={queryResults.row_count}
                    executionTime={queryResults.execution_time_ms}
                  />
                </CardContent>
              </Card>
            )}

            {/* Empty State */}
            {!loadingSnapshots && snapshots.length === 0 && !error && (
              <Card>
                <CardContent className="py-12 text-center">
                  <Layers className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
                  <h3 className="text-xl font-semibold mb-2">No Snapshots Yet</h3>
                  <p className="text-muted-foreground mb-4">
                    Enter a table path and click "Load Snapshots" to view history
                  </p>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Right: Info & Guide */}
          <div className="space-y-6">
            {/* Selected Snapshot Info */}
            {selectedSnapshot && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Calendar className="h-5 w-5 text-orange-500" />
                    Selected Snapshot
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <div>
                    <div className="text-muted-foreground">Snapshot ID</div>
                    <div className="font-mono font-medium">{selectedSnapshot.snapshot_id}</div>
                  </div>
                  {selectedSnapshot.timestamp && (
                    <div>
                      <div className="text-muted-foreground">Created</div>
                      <div>{formatTimestamp(selectedSnapshot.timestamp)}</div>
                    </div>
                  )}
                  {selectedSnapshot.operation && (
                    <div>
                      <div className="text-muted-foreground">Operation</div>
                      <div>{selectedSnapshot.operation}</div>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Time Travel Guide */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Clock className="h-5 w-5 text-blue-500" />
                  Time Travel Guide
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div>
                  <div className="font-medium mb-1">What is Time Travel?</div>
                  <div className="text-muted-foreground">
                    Query any historical version of your data using snapshot IDs.
                  </div>
                </div>
                <div>
                  <div className="font-medium mb-1">Query Syntax</div>
                  <div className="font-mono text-xs bg-muted p-2 rounded">
                    FOR VERSION AS OF [snapshot_id]
                  </div>
                </div>
                <div>
                  <div className="font-medium mb-1">Use Cases</div>
                  <ul className="list-disc list-inside text-muted-foreground space-y-1">
                    <li>Audit data changes</li>
                    <li>Recover deleted records</li>
                    <li>Compare versions</li>
                    <li>Reproduce reports</li>
                  </ul>
                </div>
              </CardContent>
            </Card>

            {/* Snapshot Info */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">About Snapshots</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm text-muted-foreground">
                <p>
                  Delta Lake creates a new snapshot for every write operation (INSERT, UPDATE, DELETE).
                </p>
                <p>
                  Each snapshot is immutable and contains metadata about the table state at that point in time.
                </p>
                <p>
                  Snapshots enable ACID transactions and allow you to query historical data without additional storage cost.
                </p>
              </CardContent>
            </Card>

            {/* Tips */}
            <Alert variant="info">
              <AlertTitle>💡 Pro Tips</AlertTitle>
              <AlertDescription className="text-sm mt-2 space-y-1">
                <div>• Snapshots are automatically created on write</div>
                <div>• No performance penalty for time travel queries</div>
                <div>• Use snapshot IDs for reproducible reports</div>
                <div>• Old snapshots can be cleaned with VACUUM</div>
              </AlertDescription>
            </Alert>
          </div>
        </div>
      </main>
    </div>
  );
}
