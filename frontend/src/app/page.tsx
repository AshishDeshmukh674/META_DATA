'use client';

import Link from 'next/link';
import { Database, FileSearch, MessageSquare, History } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import Navigation from '@/components/navigation';

export default function Home() {
  const features = [
    {
      title: 'Metadata Explorer',
      description: 'Generate metadata, view schema, partitions, versions, and compare snapshots',
      icon: FileSearch,
      href: '/metadata',
      color: 'from-purple-500 to-pink-500',
    },
    {
      title: 'Natural Language Queries',
      description: 'Ask questions in plain English and get SQL results automatically',
      icon: MessageSquare,
      href: '/natural-language',
      color: 'from-blue-500 to-cyan-500',
    },
    {
      title: 'SQL Query Editor',
      description: 'Write and execute SQL queries directly against your lakehouse tables',
      icon: Database,
      href: '/sql-query',
      color: 'from-green-500 to-emerald-500',
    },
    {
      title: 'Snapshot Manager',
      description: 'View and compare metadata snapshots to track table evolution',
      icon: History,
      href: '/snapshots',
      color: 'from-orange-500 to-red-500',
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/20">
      <Navigation />

      <main className="container mx-auto px-4 py-16">
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold mb-4">Lakehouse Explorer</h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Explore, query, and manage your lakehouse data with ease. 
            Support for Delta Lake, Iceberg, Hudi, and Parquet.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-6 max-w-5xl mx-auto">
          {features.map((feature) => {
            const Icon = feature.icon;
            return (
              <Link key={feature.href} href={feature.href}>
                <Card className="h-full hover:shadow-lg transition-shadow cursor-pointer">
                  <CardHeader>
                    <div className={`h-12 w-12 rounded-lg bg-gradient-to-br ${feature.color} flex items-center justify-center mb-4`}>
                      <Icon className="h-6 w-6 text-white" />
                    </div>
                    <CardTitle>{feature.title}</CardTitle>
                    <CardDescription>{feature.description}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Button variant="outline" className="w-full">
                      Get Started →
                    </Button>
                  </CardContent>
                </Card>
              </Link>
            );
          })}
        </div>

        <div className="mt-16 text-center">
          <h2 className="text-2xl font-bold mb-4">Supported Formats</h2>
          <div className="flex justify-center gap-8 flex-wrap">
            <div className="text-center">
              <div className="text-3xl font-bold text-primary">Delta Lake</div>
              <p className="text-sm text-muted-foreground">Open source</p>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-primary">Iceberg</div>
              <p className="text-sm text-muted-foreground">Open source</p>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-primary">Hudi</div>
              <p className="text-sm text-muted-foreground">Open source</p>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-primary">Parquet</div>
              <p className="text-sm text-muted-foreground">Columnar format</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
