'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { Navigation } from '@/components/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { 
  MessageSquare, 
  Database, 
  TableProperties, 
  Layers,
  Zap,
  Clock,
  ArrowRight,
  CheckCircle2,
} from 'lucide-react';
import { checkHealth } from '@/lib/api/queries';
import toast from 'react-hot-toast';

const features = [
  {
    title: 'Natural Language Queries',
    description: 'Ask questions in plain English. No SQL knowledge needed! Our AI converts your questions to SQL automatically.',
    icon: MessageSquare,
    href: '/natural-language',
    color: 'from-blue-500 to-cyan-500',
    examples: [
      'Show me all customers from Mumbai',
      'Count customers per city',
      'Find customers with gmail addresses',
    ],
  },
  {
    title: 'Fast SQL Queries',
    description: 'Execute SQL queries with Trino for lightning-fast results (100-500ms). Perfect for dashboards and analytics.',
    icon: Database,
    href: '/sql-query',
    color: 'from-purple-500 to-pink-500',
    examples: [
      'SELECT * FROM delta.default.customers',
      'GROUP BY aggregations',
      'Complex JOINs and filters',
    ],
  },
  {
    title: 'Metadata Generation',
    description: 'Convert CSV files to Delta Lake format. Automatic schema detection and snapshot management.',
    icon: TableProperties,
    href: '/metadata',
    color: 'from-green-500 to-emerald-500',
    examples: [
      'CSV → Delta conversion',
      'Schema extraction',
      'Automatic versioning',
    ],
  },
  {
    title: 'Time Travel',
    description: 'Query historical versions of your data. See what your data looked like at any point in time.',
    icon: Layers,
    href: '/snapshots',
    color: 'from-orange-500 to-red-500',
    examples: [
      'Query any snapshot',
      'Version comparison',
      'Audit trails',
    ],
  },
];

const benefits = [
  'No metastore required - Direct S3 access',
  'Dual query engines - Fast & flexible',
  'AI-powered queries - Natural language support',
  'Time travel - Query historical data',
  'Production-ready - REST API included',
  'Open source - Fully customizable',
];

export default function HomePage() {
  const [apiStatus, setApiStatus] = useState<'checking' | 'online' | 'offline'>('checking');

  useEffect(() => {
    checkHealth()
      .then(() => {
        setApiStatus('online');
        toast.success('Connected to Lakehouse API');
      })
      .catch(() => {
        setApiStatus('offline');
        toast.error('Unable to connect to API. Is the server running?');
      });
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/20">
      <Navigation />
      
      <main className="container mx-auto px-4 py-12">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary mb-6">
            <Zap className="h-4 w-4" />
            <span className="text-sm font-medium">AI-Powered Data Platform</span>
          </div>
          
          <h1 className="text-5xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
            Lakehouse Explorer
          </h1>
          
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            Query your Delta Lake data using natural language or SQL. 
            No metastore required, no complex setup. Just connect and query.
          </p>

          {/* API Status */}
          <div className="flex items-center justify-center gap-2 mb-8">
            <div className={`h-3 w-3 rounded-full ${
              apiStatus === 'online' ? 'bg-green-500 animate-pulse' :
              apiStatus === 'offline' ? 'bg-red-500' :
              'bg-yellow-500 animate-pulse'
            }`} />
            <span className="text-sm text-muted-foreground">
              API Status: {apiStatus === 'online' ? 'Connected' : apiStatus === 'offline' ? 'Offline' : 'Checking...'}
            </span>
          </div>

          <div className="flex items-center justify-center gap-4">
            <Link href="/natural-language">
              <Button size="lg" className="gap-2">
                Try Natural Language Query
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link href="/sql-query">
              <Button size="lg" variant="outline" className="gap-2">
                SQL Query Editor
                <Database className="h-4 w-4" />
              </Button>
            </Link>
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-2 gap-6 mb-16">
          {features.map((feature) => {
            const Icon = feature.icon;
            return (
              <Card key={feature.title} className="card-hover group">
                <CardHeader>
                  <div className={`h-12 w-12 rounded-lg bg-gradient-to-br ${feature.color} flex items-center justify-center mb-4`}>
                    <Icon className="h-6 w-6 text-white" />
                  </div>
                  <CardTitle>{feature.title}</CardTitle>
                  <CardDescription>{feature.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 mb-4">
                    {feature.examples.map((example, index) => (
                      <div key={index} className="text-sm text-muted-foreground flex items-start gap-2">
                        <CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                        <span>{example}</span>
                      </div>
                    ))}
                  </div>
                  <Link href={feature.href}>
                    <Button variant="ghost" className="w-full group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                      Get Started <ArrowRight className="ml-2 h-4 w-4" />
                    </Button>
                  </Link>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Benefits Section */}
        <Card className="mb-16">
          <CardHeader>
            <CardTitle className="text-2xl">Why Choose Lakehouse Explorer?</CardTitle>
            <CardDescription>
              Modern data platform built for speed, simplicity, and flexibility
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-3 gap-4">
              {benefits.map((benefit, index) => (
                <div key={index} className="flex items-start gap-3">
                  <CheckCircle2 className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
                  <span className="text-sm">{benefit}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Quick Start */}
        <Alert variant="info">
          <AlertTitle className="flex items-center gap-2">
            <Clock className="h-4 w-4" />
            Quick Start
          </AlertTitle>
          <AlertDescription>
            <ol className="list-decimal list-inside space-y-2 mt-2 text-sm">
              <li>Generate metadata from your CSV files</li>
              <li>Sync tables with Trino for fast queries</li>
              <li>Start querying with natural language or SQL</li>
            </ol>
          </AlertDescription>
        </Alert>
      </main>
    </div>
  );
}
