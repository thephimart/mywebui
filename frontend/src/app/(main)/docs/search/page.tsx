'use client';

import { useState } from 'react';
import { searchDocuments } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useCapabilities } from '@/hooks/useCapabilities';
import { FeatureUnavailable } from '@/components/FeatureUnavailable';
import type { SearchResult } from '@/types/api';

export default function SearchPage() {
  const { capabilities } = useCapabilities();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;
    setIsLoading(true);
    setHasSearched(true);
    try {
      const res = await searchDocuments({ query, limit: 10, category: null });
      setResults(res.results);
    } catch (err) {
      console.error('Search failed:', err);
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  if (!capabilities?.filesystem?.enabled && !capabilities?.web?.enabled) {
    return <FeatureUnavailable feature="Search" message="No storage capabilities available." />;
  }

  return (
    <div className="container mx-auto py-8">
      <h1 className="text-2xl font-semibold mb-6">Search Documents</h1>

      <div className="flex gap-2 mb-8">
        <Input
          placeholder="Search your documents..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          className="flex-1"
        />
        <Button onClick={handleSearch} disabled={isLoading || !query.trim()}>
          {isLoading ? 'Searching...' : 'Search'}
        </Button>
      </div>

      {!hasSearched ? (
        <div className="text-center py-8 text-muted-foreground">
          Enter a query to search your documents.
        </div>
      ) : results.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground">
          No results found.
        </div>
      ) : (
        <div className="space-y-4">
          {results.map((result) => (
            <Card key={result.chunk_id}>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">
                    Document: {result.document_id.slice(0, 8)}...
                  </CardTitle>
                  <span className="text-sm text-muted-foreground">
                    Score: {(result.score * 100).toFixed(1)}%
                  </span>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm">{result.text}</p>
                <div className="mt-2">
                  <span className="text-xs text-muted-foreground">Type: {result.modality}</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
