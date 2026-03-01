'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Database, MessageSquare, FileSearch, History, Settings as SettingsIcon } from 'lucide-react';

export default function Navigation() {
  const pathname = usePathname();

  const links = [
    { href: '/', label: 'Home', icon: Database },
    { href: '/metadata', label: 'Metadata Explorer', icon: FileSearch },
    { href: '/natural-language', label: 'Natural Language', icon: MessageSquare },
    { href: '/sql-query', label: 'SQL Query', icon: Database },
    { href: '/snapshots', label: 'Snapshots', icon: History },
    { href: '/settings', label: 'Settings', icon: SettingsIcon },
  ];

  return (
    <nav className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center gap-2">
            <Database className="h-6 w-6 text-primary" />
            <span className="text-xl font-bold">Lakehouse Explorer</span>
          </div>
          <div className="flex gap-1">
            {links.map((link) => {
              const Icon = link.icon;
              const isActive = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  {link.label}
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </nav>
  );
}
