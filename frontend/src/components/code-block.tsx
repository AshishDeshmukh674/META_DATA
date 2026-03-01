'use client';

import { useState } from 'react';
import { Check, Copy } from 'lucide-react';
import { Button } from './ui/button';

interface CodeBlockProps {
  code: string;
  language?: string;
}

export function CodeBlock({ code, language = 'json' }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative">
      <Button
        variant="ghost"
        size="icon"
        className="absolute right-2 top-2 h-8 w-8"
        onClick={handleCopy}
      >
        {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
      </Button>
      <pre className="overflow-auto rounded-lg bg-muted p-4 text-sm">
        <code className={`language-${language}`}>{code}</code>
      </pre>
    </div>
  );
}
