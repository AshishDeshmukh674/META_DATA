'use client';

import { useState, useEffect } from 'react';
import { History, GitBranch, Clock, FileText, AlertCircle, GitCompare } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert } from '@/components/ui/alert';
import { Loading } from '@/components/ui/loading';
import { CodeBlock } from '@/components/code-block';
import Navigation from '@/components/Navigation';
import toast from 'react-hot-toast';
import { listSnapshots, getLatestSnapshot, generateMetadata, compareSnapshots } from '@/lib/api/queries';

export default function SnapshotsPage() {
  const [storageType, setStorageType] = useState<'aws' | 'minio'>('aws');
  const [bucketName, setBucketName] = useState('metadataproject');
  const [tablePath, setTablePath] = useState('test-data/customer_data/customer_data_delta');
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [snapshots, setSnapshots] = useState<any[]>([]);
  const [selectedSnapshot, setSelectedSnapshot] = useState<any>(null);
  
  // Comparison state
  const [showCompare, setShowCompare] = useState(false);
  const [snapshotId1, setSnapshotId1] = useState('');
  const [snapshotId2, setSnapshotId2] = useState('');
  const [compareResult, setCompareResult] = useState<any>(null);

  const loadSnapshots = async () => {
    if (!tablePath.trim()) {
      toast.error('Please enter a table path');
      return;
    }

    setLoading(true);
    setError('');
    setSnapshots([]);
    setSelectedSnapshot(null);

    try {
      const response = await listSnapshots(storageType, bucketName, tablePath);
      setSnapshots(response.snapshots || []);
      
      if (response.snapshots && response.snapshots.length > 0) {
        toast.success(`Found ${response.snapshots.length} snapshot(s)`);
      } else {
        toast.info('No snapshots found for this table');
      }
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to load snapshots';
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const loadLatestSnapshot = async () => {
    if (!tablePath.trim()) {
      toast.error('Please enter a table path');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await getLatestSnapshot(storageType, bucketName, tablePath);
      setSelectedSnapshot(response);
      toast.success('Latest snapshot loaded');
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to load latest snapshot';
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const createNewSnapshot = async () => {
    if (!tablePath.trim()) {
      toast.error('Please enter a table path');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await generateMetadata({
        storage_type: storageType,
        bucket: bucketName,
        path: tablePath,
        table_format: 'delta',
        force_refresh: true,
      });

      toast.success(`New snapshot created: ${response.snapshot_id}`);
      // Reload snapshots list
      await loadSnapshots();
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to create snapshot';
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const viewSnapshot = (snapshot: any) => {
    setSelectedSnapshot(snapshot);
  };

  const handleCompareSnapshots = async () => {
    if (!snapshotId1.trim() || !snapshotId2.trim()) {
      toast.error('Please enter both snapshot IDs');
      return;
    }

    setLoading(true);
    setError('');
    setCompareResult(null);

    try {
      const response = await compareSnapshots({
        storage_type: storageType,
        bucket: bucketName,
        path: tablePath,
        snapshot_id_1: snapshotId1,
        snapshot_id_2: snapshotId2,
      });

      setCompareResult(response);
      toast.success('Snapshots compared successfully');
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to compare snapshots';
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      return new Date(timestamp).toLocaleString();
    } catch {
      return timestamp;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/20">
      <Navigation />

      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-3 rounded-lg bg-primary/10">
              <History className="h-8 w-8 text-primary" />
            </div>
            <div>
              <h1 className="text-3xl font-bold">Metadata Snapshots</h1>
              <p className="text-muted-foreground">View and manage table metadata snapshots</p>
            </div>
          </div>
        </div>

        <div className="grid gap-6 max-w-6xl mx-auto">
          {/* Configuration Card */}
          <Card>
            <CardHeader>
              <CardTitle>Table Configuration</CardTitle>
              <CardDescription>Select the table to view snapshots</CardDescription>
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
                <Label htmlFor="tablePath">Table Path</Label>
                <Input
                  id="tablePath"
                  value={tablePath}
                  onChange={(e) => setTablePath(e.target.value)}
                  placeholder="path/to/table"
                />
              </div>

              <div className="flex gap-3">
                <Button 
                  onClick={loadSnapshots} 
                  disabled={loading}
                  className="flex-1"
                >
                  {loading ? (
                    <>
                      <Loading size="sm" className="mr-2" />
                      Loading...
                    </>
                  ) : (
                    <>
                      <FileText className="mr-2 h-4 w-4" />
                      List Snapshots
                    </>
                  )}
                </Button>
                
                <Button 
                  onClick={loadLatestSnapshot} 
                  disabled={loading}
                  variant="outline"
                >
                  <Clock className="mr-2 h-4 w-4" />
                  Latest Snapshot
                </Button>

                <Button 
                  onClick={createNewSnapshot} 
                  disabled={loading}
                  variant="outline"
                >
                  <GitBranch className="mr-2 h-4 w-4" />
                  Create New
                </Button>

                <Button 
                  onClick={() => setShowCompare(!showCompare)} 
                  variant="outline"
                >
                  <GitCompare className="mr-2 h-4 w-4" />
                  Compare
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Compare Snapshots Section */}
          {showCompare && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <GitCompare className="h-5 w-5" />
                  Compare Snapshots
                </CardTitle>
                <CardDescription>
                  Compare two metadata snapshots to see differences
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {snapshots.length === 0 ? (
                  <Alert>
                    <AlertCircle className="h-4 w-4" />
                    <p className="text-sm">Please load snapshots first using the "List Snapshots" button above.</p>
                  </Alert>
                ) : (
                  <>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="snapshotId1">First Snapshot</Label>
                        <select
                          id="snapshotId1"
                          value={snapshotId1}
                          onChange={(e) => setSnapshotId1(e.target.value)}
                          className="w-full rounded-md border border-input bg-background px-3 py-2"
                        >
                          <option value="">Select first snapshot...</option>
                          {snapshots.map((snapshot, index) => (
                            <option key={index} value={snapshot.snapshot_id}>
                              {snapshot.snapshot_id} ({snapshot.timestamp ? formatTimestamp(snapshot.timestamp) : 'Unknown date'})
                            </option>
                          ))}
                        </select>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="snapshotId2">Second Snapshot</Label>
                        <select
                          id="snapshotId2"
                          value={snapshotId2}
                          onChange={(e) => setSnapshotId2(e.target.value)}
                          className="w-full rounded-md border border-input bg-background px-3 py-2"
                        >
                          <option value="">Select second snapshot...</option>
                          {snapshots.map((snapshot, index) => (
                            <option key={index} value={snapshot.snapshot_id}>
                              {snapshot.snapshot_id} ({snapshot.timestamp ? formatTimestamp(snapshot.timestamp) : 'Unknown date'})
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>

                    {snapshots.length < 2 && (
                      <Alert>
                        <AlertCircle className="h-4 w-4" />
                        <p className="text-sm">At least 2 snapshots are required for comparison. Only {snapshots.length} snapshot(s) found.</p>
                      </Alert>
                    )}

                    <Button 
                      onClick={handleCompareSnapshots} 
                      disabled={loading || !snapshotId1 || !snapshotId2 || snapshots.length < 2}
                      className="w-full"
                    >
                      {loading ? (
                        <>
                          <Loading size="sm" className="mr-2" />
                          Comparing...
                        </>
                      ) : (
                        <>
                          <GitCompare className="mr-2 h-4 w-4" />
                          Compare Snapshots
                        </>
                      )}
                    </Button>
                  </>
                )}
              </CardContent>
            </Card>
          )}

          {/* Comparison Results */}
          {compareResult && (
            <Card>
              <CardHeader>
                <CardTitle>Comparison Results</CardTitle>
                <CardDescription>
                  Differences between {snapshotId1} and {snapshotId2}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <CodeBlock
                  code={JSON.stringify(compareResult, null, 2)}
                  language="json"
                />
              </CardContent>
            </Card>
          )}

          {/* Error Display */}
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <p className="font-semibold">Error</p>
              <p className="text-sm mt-1">{error}</p>
            </Alert>
          )}

          {/* Snapshots List */}
          {snapshots.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Available Snapshots</CardTitle>
                <CardDescription>
                  Found {snapshots.length} snapshot{snapshots.length !== 1 ? 's' : ''}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {snapshots.map((snapshot, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 cursor-pointer transition-colors"
                      onClick={() => viewSnapshot(snapshot)}
                    >
                      <div className="flex items-center gap-4">
                        <div className="p-2 rounded-lg bg-primary/10">
                          <GitBranch className="h-5 w-5 text-primary" />
                        </div>
                        <div>
                          <p className="font-medium">{snapshot.snapshot_id || `Snapshot ${index + 1}`}</p>
                          <p className="text-sm text-muted-foreground">
                            {snapshot.timestamp ? formatTimestamp(snapshot.timestamp) : 'Unknown date'}
                          </p>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          viewSnapshot(snapshot);
                        }}
                      >
                        View Details
                      </Button>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Selected Snapshot Details */}
          {selectedSnapshot && (
            <Card>
              <CardHeader>
                <CardTitle>Snapshot Details</CardTitle>
                <CardDescription>
                  {selectedSnapshot.snapshot_id || 'Snapshot Information'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <CodeBlock
                  code={JSON.stringify(selectedSnapshot, null, 2)}
                  language="json"
                />
              </CardContent>
            </Card>
          )}

          {/* Empty State */}
          {!loading && snapshots.length === 0 && !selectedSnapshot && !error && (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-16">
                <History className="h-16 w-16 text-muted-foreground/50 mb-4" />
                <h3 className="text-xl font-semibold mb-2">No Snapshots Loaded</h3>
                <p className="text-muted-foreground text-center mb-6">
                  Configure your table and click "List Snapshots" to view available metadata snapshots
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </main>
    </div>
  );
}
