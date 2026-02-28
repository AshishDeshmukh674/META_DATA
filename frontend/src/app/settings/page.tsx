'use client';

import React, { useState, useEffect } from 'react';
import { Navigation } from '@/components/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { checkHealth } from '@/lib/api/queries';
import { Settings as SettingsIcon, Activity, Database, Zap, CheckCircle2, XCircle, Info } from 'lucide-react';
import toast from 'react-hot-toast';

export default function SettingsPage() {
  // API Settings
  const [apiUrl, setApiUrl] = useState('http://localhost:8001');
  const [trinoHost, setTrinoHost] = useState('localhost');
  const [trinoPort, setTrinoPort] = useState('8080');
  
  // Default Table Config
  const [defaultStorageType, setDefaultStorageType] = useState('local');
  const [defaultBucket, setDefaultBucket] = useState('');
  const [defaultTablePath, setDefaultTablePath] = useState('C:/Users/ashis/Desktop/META/data/delta/customers');
  
  // Connection Status
  const [apiStatus, setApiStatus] = useState<'unknown' | 'checking' | 'connected' | 'failed'>('unknown');
  const [lastCheck, setLastCheck] = useState<Date | null>(null);

  // Theme
  const [theme, setTheme] = useState<'light' | 'dark' | 'system'>('system');

  useEffect(() => {
    // Load saved settings from localStorage
    const savedApiUrl = localStorage.getItem('apiUrl');
    const savedStorageType = localStorage.getItem('defaultStorageType');
    const savedBucket = localStorage.getItem('defaultBucket');
    const savedTablePath = localStorage.getItem('defaultTablePath');
    const savedTheme = localStorage.getItem('theme');

    if (savedApiUrl) setApiUrl(savedApiUrl);
    if (savedStorageType) setDefaultStorageType(savedStorageType);
    if (savedBucket) setDefaultBucket(savedBucket);
    if (savedTablePath) setDefaultTablePath(savedTablePath);
    if (savedTheme) setTheme(savedTheme as 'light' | 'dark' | 'system');

    // Check connection on load
    handleCheckConnection();
  }, []);

  const handleCheckConnection = async () => {
    setApiStatus('checking');
    
    try {
      await checkHealth();
      setApiStatus('connected');
      setLastCheck(new Date());
      toast.success('API connection successful!');
    } catch (err: any) {
      setApiStatus('failed');
      setLastCheck(new Date());
      toast.error('Failed to connect to API');
    }
  };

  const handleSaveSettings = () => {
    // Save to localStorage
    localStorage.setItem('apiUrl', apiUrl);
    localStorage.setItem('defaultStorageType', defaultStorageType);
    localStorage.setItem('defaultBucket', defaultBucket);
    localStorage.setItem('defaultTablePath', defaultTablePath);
    localStorage.setItem('theme', theme);

    toast.success('Settings saved successfully!');
  };

  const handleResetSettings = () => {
    setApiUrl('http://localhost:8001');
    setTrinoHost('localhost');
    setTrinoPort('8080');
    setDefaultStorageType('local');
    setDefaultBucket('');
    setDefaultTablePath('C:/Users/ashis/Desktop/META/data/delta/customers');
    setTheme('system');

    localStorage.clear();
    toast.success('Settings reset to defaults');
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/20">
      <Navigation />
      
      <main className="container mx-auto px-4 py-8 max-w-5xl">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-3">
            <div className="h-12 w-12 rounded-lg bg-gradient-to-br from-gray-500 to-gray-700 flex items-center justify-center">
              <SettingsIcon className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold">Settings</h1>
              <p className="text-muted-foreground">Configure your Lakehouse Explorer preferences.</p>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          {/* API Connection */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Activity className="h-5 w-5" />
                    API Connection
                  </CardTitle>
                  <CardDescription>Configure backend API endpoint</CardDescription>
                </div>
                <div className="flex items-center gap-2">
                  <div className={`h-2 w-2 rounded-full ${
                    apiStatus === 'connected' ? 'bg-green-500 animate-pulse' :
                    apiStatus === 'failed' ? 'bg-red-500' :
                    apiStatus === 'checking' ? 'bg-yellow-500 animate-pulse' :
                    'bg-gray-400'
                  }`} />
                  <span className="text-sm text-muted-foreground">
                    {apiStatus === 'connected' ? 'Connected' :
                     apiStatus === 'failed' ? 'Disconnected' :
                     apiStatus === 'checking' ? 'Checking...' :
                     'Unknown'}
                  </span>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="apiUrl">FastAPI URL</Label>
                <Input
                  id="apiUrl"
                  value={apiUrl}
                  onChange={(e) => setApiUrl(e.target.value)}
                  placeholder="http://localhost:8001"
                />
                <p className="text-xs text-muted-foreground">
                  Backend API endpoint (default: http://localhost:8001)
                </p>
              </div>

              <div className="flex gap-3">
                <Button onClick={handleCheckConnection} variant="outline">
                  <Activity className="mr-2 h-4 w-4" />
                  Test Connection
                </Button>
                {lastCheck && (
                  <span className="text-sm text-muted-foreground self-center">
                    Last checked: {lastCheck.toLocaleTimeString()}
                  </span>
                )}
              </div>

              {apiStatus === 'connected' && (
                <Alert variant="success">
                  <CheckCircle2 className="h-4 w-4" />
                  <AlertTitle>Connected</AlertTitle>
                  <AlertDescription>
                    Successfully connected to FastAPI backend
                  </AlertDescription>
                </Alert>
              )}

              {apiStatus === 'failed' && (
                <Alert variant="destructive">
                  <XCircle className="h-4 w-4" />
                  <AlertTitle>Connection Failed</AlertTitle>
                  <AlertDescription>
                    Unable to reach the API. Make sure the backend server is running on port 8001.
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>

          {/* Trino Configuration */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-5 w-5" />
                Trino Configuration
              </CardTitle>
              <CardDescription>Trino query engine settings (read-only)</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="trinoHost">Trino Host</Label>
                  <Input
                    id="trinoHost"
                    value={trinoHost}
                    onChange={(e) => setTrinoHost(e.target.value)}
                    placeholder="localhost"
                    disabled
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="trinoPort">Trino Port</Label>
                  <Input
                    id="trinoPort"
                    value={trinoPort}
                    onChange={(e) => setTrinoPort(e.target.value)}
                    placeholder="8080"
                    disabled
                  />
                </div>
              </div>
              <Alert variant="info">
                <Info className="h-4 w-4" />
                <AlertDescription className="text-sm">
                  Trino configuration is managed by the backend. Runs on Docker at localhost:8080.
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>

          {/* Default Table Configuration */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-5 w-5" />
                Default Table Configuration
              </CardTitle>
              <CardDescription>Set defaults for table operations</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="defaultStorageType">Storage Type</Label>
                <select
                  id="defaultStorageType"
                  value={defaultStorageType}
                  onChange={(e) => setDefaultStorageType(e.target.value)}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <option value="local">Local Filesystem</option>
                  <option value="s3">Amazon S3</option>
                </select>
              </div>

              {defaultStorageType === 's3' && (
                <div className="space-y-2">
                  <Label htmlFor="defaultBucket">Default S3 Bucket</Label>
                  <Input
                    id="defaultBucket"
                    value={defaultBucket}
                    onChange={(e) => setDefaultBucket(e.target.value)}
                    placeholder="my-data-bucket"
                  />
                </div>
              )}

              <div className="space-y-2">
                <Label htmlFor="defaultTablePath">Default Table Path</Label>
                <Input
                  id="defaultTablePath"
                  value={defaultTablePath}
                  onChange={(e) => setDefaultTablePath(e.target.value)}
                  placeholder="C:/path/to/delta/table"
                />
              </div>
            </CardContent>
          </Card>

          {/* Appearance */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="h-5 w-5" />
                Appearance
              </CardTitle>
              <CardDescription>Customize the UI theme</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="theme">Theme</Label>
                <select
                  id="theme"
                  value={theme}
                  onChange={(e) => setTheme(e.target.value as 'light' | 'dark' | 'system')}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <option value="system">System Default</option>
                  <option value="light">Light</option>
                  <option value="dark">Dark</option>
                </select>
              </div>
              <Alert variant="info">
                <Info className="h-4 w-4" />
                <AlertDescription className="text-sm">
                  Theme changes will apply on next page load.
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>

          {/* Actions */}
          <Card>
            <CardHeader>
              <CardTitle>Actions</CardTitle>
              <CardDescription>Manage your settings</CardDescription>
            </CardHeader>
            <CardContent className="flex gap-3">
              <Button onClick={handleSaveSettings} className="flex-1">
                <CheckCircle2 className="mr-2 h-4 w-4" />
                Save Settings
              </Button>
              <Button onClick={handleResetSettings} variant="outline">
                Reset to Defaults
              </Button>
            </CardContent>
          </Card>

          {/* System Information */}
          <Card>
            <CardHeader>
              <CardTitle>System Information</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 gap-4 text-sm">
                <div>
                  <div className="text-muted-foreground mb-1">Version</div>
                  <div className="font-mono">1.0.0</div>
                </div>
                <div>
                  <div className="text-muted-foreground mb-1">Framework</div>
                  <div>Next.js 14</div>
                </div>
                <div>
                  <div className="text-muted-foreground mb-1">Backend</div>
                  <div>FastAPI + Trino</div>
                </div>
                <div>
                  <div className="text-muted-foreground mb-1">Storage</div>
                  <div>Delta Lake</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
