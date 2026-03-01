'use client';

import { useState } from 'react';
import toast from 'react-hot-toast';
import { 
  Database, 
  FileText, 
  GitBranch, 
  FolderTree, 
  FileCode, 
  GitCompare,
  Sparkles
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Loading } from '@/components/ui/loading';
import { Alert } from '@/components/ui/alert';
import { CodeBlock } from '@/components/code-block';
import { DataTable } from '@/components/data-table';
import Navigation from '@/components/navigation';
import {
  generateMetadata,
  getSchema,
  getPartitions,
  getSnapshots as getSnapshotsAPI,
  getFiles,
  compareSnapshots,
  listSnapshots
} from '@/lib/api/queries';

type TabType = 'generate' | 'schema' | 'partitions' | 'snapshots' | 'files' | 'diff';

export default function MetadataPage() {
  const [activeTab, setActiveTab] = useState<TabType>('generate');
  
  // Common inputs
  const [storageType, setStorageType] = useState<'aws' | 'minio'>('aws');
  const [bucketName, setBucketName] = useState('metadataproject');
  const [tablePath, setTablePath] = useState('test-data/customer_data/customer_data_delta');
  const [tableFormat, setTableFormat] = useState<'delta' | 'iceberg' | 'hudi' | 'parquet' | ''>('');
  
  // Generate tab specific
  const [csvPath, setCsvPath] = useState('test-data/customer_data/customer_data.csv');
  const [forceRefresh, setForceRefresh] = useState(false);
  
  // Diff tab specific
  const [snapshotId1, setSnapshotId1] = useState('');
  const [snapshotId2, setSnapshotId2] = useState('');
  const [availableSnapshots, setAvailableSnapshots] = useState<any[]>([]);
  
  // Loading and results
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<any>(null);

  const tabs = [
    { id: 'generate' as TabType, label: 'Generate Metadata', icon: Sparkles, description: 'Convert CSV to Delta and generate metadata' },
    { id: 'schema' as TabType, label: 'Schema', icon: FileCode, description: 'View table schema and column types' },
    { id: 'partitions' as TabType, label: 'Partitions', icon: FolderTree, description: 'View table partitioning info' },
    { id: 'snapshots' as TabType, label: 'Versions', icon: GitBranch, description: 'View table version history' },
    { id: 'files' as TabType, label: 'Files', icon: FileText, description: 'List data files in the table' },
    { id: 'diff' as TabType, label: 'Compare Snapshots', icon: GitCompare, description: 'Compare two metadata snapshots' },
  ];

  const handleGenerate = async () => {
    if (!csvPath.trim()) {
      toast.error('Please enter a file path');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await generateMetadata({
        storage_type: storageType,
        bucket: bucketName,
        path: csvPath,
        table_format: 'delta',
        force_refresh: forceRefresh,
      });

      setResult(response);
      toast.success(`Metadata generated! Snapshot: ${response.snapshot_id}`);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Metadata generation failed';
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleGetSchema = async () => {
    if (!tablePath.trim()) {
      toast.error('Please enter a table path');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await getSchema({
        storage_type: storageType,
        bucket: bucketName,
        path: tablePath,
        format: tableFormat || undefined,
      });

      setResult(response);
      toast.success('Schema retrieved successfully!');
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to get schema';
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleGetPartitions = async () => {
    if (!tablePath.trim()) {
      toast.error('Please enter a table path');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await getPartitions({
        storage_type: storageType,
        bucket: bucketName,
        path: tablePath,
        format: tableFormat || undefined,
      });

      setResult(response);
      toast.success('Partitions retrieved successfully!');
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to get partitions';
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleGetSnapshots = async () => {
    if (!tablePath.trim()) {
      toast.error('Please enter a table path');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await getSnapshotsAPI({
        storage_type: storageType,
        bucket: bucketName,
        path: tablePath,
        format: tableFormat || undefined,
      });

      setResult(response);
      toast.success('Snapshots retrieved successfully!');
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to get snapshots';
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleGetFiles = async () => {
    if (!tablePath.trim()) {
      toast.error('Please enter a table path');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await getFiles({
        storage_type: storageType,
        bucket: bucketName,
        path: tablePath,
        format: tableFormat || undefined,
      });

      setResult(response);
      toast.success('Files retrieved successfully!');
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to get files';
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleLoadSnapshots = async () => {
    if (!tablePath.trim()) {
      toast.error('Please enter a table path');
      return;
    }

    setLoading(true);
    try {
      const response = await listSnapshots(storageType, bucketName, tablePath);
      setAvailableSnapshots(response.snapshots || []);
      toast.success(`Loaded ${response.snapshots?.length || 0} snapshots`);
    } catch (err: any) {
      toast.error('Failed to load snapshots');
    } finally {
      setLoading(false);
    }
  };

  const handleCompareSnapshots = async () => {
    if (!tablePath.trim() || !snapshotId1 || !snapshotId2) {
      toast.error('Please enter table path and select two snapshots');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await compareSnapshots({
        storage_type: storageType,
        bucket: bucketName,
        path: tablePath,
        snapshot_id_1: snapshotId1,
        snapshot_id_2: snapshotId2,
      });

      setResult(response);
      toast.success('Snapshots compared successfully!');
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to compare snapshots';
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const renderCommonInputs = () => (
    <>
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
        <Label htmlFor="tableFormat">
          Table Format <span className="text-muted-foreground text-sm">(optional - auto-detect if empty)</span>
        </Label>
        <select
          id="tableFormat"
          value={tableFormat}
          onChange={(e) => setTableFormat(e.target.value as any)}
          className="w-full rounded-md border border-input bg-background px-3 py-2"
        >
          <option value="">Auto-detect</option>
          <option value="delta">Delta Lake</option>
          <option value="iceberg">Apache Iceberg</option>
          <option value="hudi">Apache Hudi</option>
          <option value="parquet">Parquet</option>
        </select>
      </div>
    </>
  );

  const renderTabContent = () => {
    switch (activeTab) {
      case 'generate':
        return (
          <div className="space-y-4">
            <Alert>
              <p className="text-sm">
                <strong>Generate Metadata:</strong> Convert CSV files to Delta Lake format and generate a metadata snapshot.
                The snapshot includes schema, partitions,files, and version information.
              </p>
            </Alert>

            {renderCommonInputs()}

            <div className="space-y-2">
              <Label htmlFor="csvPath">CSV File Path</Label>
              <Input
                id="csvPath"
                value={csvPath}
                onChange={(e) => setCsvPath(e.target.value)}
                placeholder="path/to/file.csv"
              />
              <p className="text-xs text-muted-foreground">
                Path to the CSV file within your bucket (e.g., test-data/customer_data/customer_data.csv)
              </p>
            </div>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="forceRefresh"
                checked={forceRefresh}
                onChange={(e) => setForceRefresh(e.target.checked)}
                className="rounded"
              />
              <Label htmlFor="forceRefresh" className="cursor-pointer">
                Force refresh (regenerate even if snapshot exists)
              </Label>
            </div>

            <Button onClick={handleGenerate} disabled={loading} className="w-full">
              {loading ? <Loading size="sm" /> : 'Generate Metadata'}
            </Button>
          </div>
        );

      case 'schema':
        return (
          <div className="space-y-4">
            <Alert>
              <p className="text-sm">
                <strong>View Schema:</strong> Get table schema including column names, data types, and nullability.
                Works with Delta, Iceberg, Hudi, and Parquet tables.
              </p>
            </Alert>

            {renderCommonInputs()}

            <div className="space-y-2">
              <Label htmlFor="tablePath">Table Path</Label>
              <Input
                id="tablePath"
                value={tablePath}
                onChange={(e) => setTablePath(e.target.value)}
                placeholder="path/to/table"
              />
              <p className="text-xs text-muted-foreground">
                Path to the lakehouse table within your bucket
              </p>
            </div>

            <Button onClick={handleGetSchema} disabled={loading} className="w-full">
              {loading ? <Loading size="sm" /> : 'Get Schema'}
            </Button>
          </div>
        );

      case 'partitions':
        return (
          <div className="space-y-4">
            <Alert>
              <p className="text-sm">
                <strong>View Partitions:</strong> Get table partitioning information including partition columns
                and values. Helps understand data organization and query optimization.
              </p>
            </Alert>

            {renderCommonInputs()}

            <div className="space-y-2">
              <Label htmlFor="tablePath">Table Path</Label>
              <Input
                id="tablePath"
                value={tablePath}
                onChange={(e) => setTablePath(e.target.value)}
                placeholder="path/to/table"
              />
            </div>

            <Button onClick={handleGetPartitions} disabled={loading} className="w-full">
              {loading ? <Loading size="sm" /> : 'Get Partitions'}
            </Button>
          </div>
        );

      case 'snapshots':
        return (
          <div className="space-y-4">
            <Alert>
              <p className="text-sm">
                <strong>View Versions:</strong> See the version history of your table. Each version represents
                a point-in-time snapshot with its own schema and data files.
              </p>
            </Alert>

            {renderCommonInputs()}

            <div className="space-y-2">
              <Label htmlFor="tablePath">Table Path</Label>
              <Input
                id="tablePath"
                value={tablePath}
                onChange={(e) => setTablePath(e.target.value)}
                placeholder="path/to/table"
              />
            </div>

            <Button onClick={handleGetSnapshots} disabled={loading} className="w-full">
              {loading ? <Loading size="sm" /> : 'Get Snapshots'}
            </Button>
          </div>
        );

      case 'files':
        return (
          <div className="space-y-4">
            <Alert>
              <p className="text-sm">
                <strong>View Files:</strong> List all data files in the table with their sizes and paths.
                Useful for debugging and understanding table storage layout.
              </p>
            </Alert>

            {renderCommonInputs()}

            <div className="space-y-2">
              <Label htmlFor="tablePath">Table Path</Label>
              <Input
                id="tablePath"
                value={tablePath}
                onChange={(e) => setTablePath(e.target.value)}
                placeholder="path/to/table"
              />
            </div>

            <Button onClick={handleGetFiles} disabled={loading} className="w-full">
              {loading ? <Loading size="sm" /> : 'Get Files'}
            </Button>
          </div>
        );

      case 'diff':
        return (
          <div className="space-y-4">
            <Alert>
              <p className="text-sm">
                <strong>Compare Snapshots:</strong> Compare two metadata snapshots to see schema changes,
                file count changes, and data size changes. Useful for tracking table evolution.
              </p>
            </Alert>

            {renderCommonInputs()}

            <div className="space-y-2">
              <Label htmlFor="tablePath">Table Path</Label>
              <Input
                id="tablePath"
                value={tablePath}
                onChange={(e) => setTablePath(e.target.value)}
                placeholder="path/to/table"
              />
            </div>

            <Button onClick={handleLoadSnapshots} disabled={loading} variant="outline" className="w-full">
              {loading ? <Loading size="sm" /> : 'Load Available Snapshots'}
            </Button>

            {availableSnapshots.length > 0 && (
              <>
                <div className="space-y-2">
                  <Label htmlFor="snapshot1">First Snapshot (Older)</Label>
                  <select
                    id="snapshot1"
                    value={snapshotId1}
                    onChange={(e) => setSnapshotId1(e.target.value)}
                    className="w-full rounded-md border border-input bg-background px-3 py-2"
                  >
                    <option value="">Select snapshot...</option>
                    {availableSnapshots.map((snap) => (
                      <option key={snap.snapshot_id} value={snap.snapshot_id}>
                        {snap.snapshot_id} ({new Date(snap.timestamp).toLocaleString()})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="snapshot2">Second Snapshot (Newer)</Label>
                  <select
                    id="snapshot2"
                    value={snapshotId2}
                    onChange={(e) => setSnapshotId2(e.target.value)}
                    className="w-full rounded-md border border-input bg-background px-3 py-2"
                  >
                    <option value="">Select snapshot...</option>
                    {availableSnapshots.map((snap) => (
                      <option key={snap.snapshot_id} value={snap.snapshot_id}>
                        {snap.snapshot_id} ({new Date(snap.timestamp).toLocaleString()})
                      </option>
                    ))}
                  </select>
                </div>

                <Button onClick={handleCompareSnapshots} disabled={loading || !snapshotId1 || !snapshotId2} className="w-full">
                  {loading ? <Loading size="sm" /> : 'Compare Snapshots'}
                </Button>
              </>
            )}
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/20">
      <Navigation />

      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-3">
            <div className="h-12 w-12 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
              <Database className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold">Metadata Explorer</h1>
              <p className="text-muted-foreground">
                Explore table metadata, schema, partitions, versions, and compare snapshots
              </p>
            </div>
          </div>
        </div>

        <div className="grid lg:grid-cols-4 gap-6">
          {/* Sidebar - Tabs */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Operations</CardTitle>
                <CardDescription>Select an operation</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                {tabs.map((tab) => {
                  const Icon = tab.icon;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => {
                        setActiveTab(tab.id);
                        setError('');
                        setResult(null);
                      }}
                      className={`w-full text-left px-4 py-3 rounded-lg transition-colors ${
                        activeTab === tab.id
                          ? 'bg-primary text-primary-foreground'
                          : 'hover:bg-muted'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <Icon className="h-4 w-4" />
                        <span className="font-medium text-sm">{tab.label}</span>
                      </div>
                      <p className="text-xs mt-1 opacity-80">{tab.description}</p>
                    </button>
                  );
                })}
              </CardContent>
            </Card>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3 space-y-6">
            {/* Input Form */}
            <Card>
              <CardHeader>
                <CardTitle>{tabs.find(t => t.id === activeTab)?.label}</CardTitle>
                <CardDescription>{tabs.find(t => t.id === activeTab)?.description}</CardDescription>
              </CardHeader>
              <CardContent>
                {renderTabContent()}
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
              <Card>
                <CardHeader>
                  <CardTitle>Results</CardTitle>
                </CardHeader>
                <CardContent>
                  <CodeBlock code={JSON.stringify(result, null, 2)} language="json" />
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
