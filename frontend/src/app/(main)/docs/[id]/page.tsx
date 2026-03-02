'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { getDocument, updateDocument, deleteDocument } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useCapabilities } from '@/hooks/useCapabilities';
import { FeatureUnavailable } from '@/components/FeatureUnavailable';
import type { Document } from '@/types/api';

export default function DocumentPage() {
  const params = useParams();
  const router = useRouter();
  const { capabilities } = useCapabilities();
  const [document, setDocument] = useState<Document | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState('');
  const [editVisibility, setEditVisibility] = useState<'private' | 'public'>('private');

  const docId = params.id as string;

  useEffect(() => {
    async function load() {
      setIsLoading(true);
      try {
        const doc = await getDocument(docId);
        setDocument(doc);
        setEditTitle(doc.title);
        setEditVisibility(doc.visibility);
      } catch (err) {
        console.error('Failed to load document:', err);
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, [docId]);

  const handleSave = async () => {
    try {
      await updateDocument(docId, {
        title: editTitle,
        visibility: editVisibility,
      });
      setDocument({ ...document!, title: editTitle, visibility: editVisibility });
      setIsEditing(false);
    } catch (err) {
      console.error('Failed to update document:', err);
    }
  };

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this document?')) return;
    try {
      await deleteDocument(docId);
      router.push('/docs');
    } catch (err) {
      console.error('Failed to delete document:', err);
    }
  };

  if (!capabilities?.filesystem?.enabled && !capabilities?.web?.enabled) {
    return <FeatureUnavailable feature="Documents" message="No storage capabilities available." />;
  }

  if (isLoading) {
    return <div className="container mx-auto py-8">Loading...</div>;
  }

  if (!document) {
    return <div className="container mx-auto py-8">Document not found</div>;
  }

  return (
    <div className="container mx-auto py-8">
      <div className="flex items-center justify-between mb-6">
        <Button variant="ghost" onClick={() => router.push('/docs')}>
          &larr; Back to Documents
        </Button>
        <div className="flex gap-2">
          {isEditing ? (
            <>
              <Button variant="outline" onClick={() => setIsEditing(false)}>Cancel</Button>
              <Button onClick={handleSave}>Save</Button>
            </>
          ) : (
            <>
              <Button variant="outline" onClick={() => setIsEditing(true)}>Edit</Button>
              <Button variant="destructive" onClick={handleDelete}>Delete</Button>
            </>
          )}
        </div>
      </div>

      <Card>
        <CardHeader>
          {isEditing ? (
            <Input
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              className="text-xl font-semibold"
            />
          ) : (
            <CardTitle className="text-xl">{document.title}</CardTitle>
          )}
          <div className="flex gap-2 mt-2">
            <Badge variant="outline">{document.visibility}</Badge>
            {document.categories.map((cat) => (
              <Badge key={cat} variant="secondary">{cat}</Badge>
            ))}
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Created: {new Date(document.created_at).toLocaleString()}
            {document.updated_at && ` | Updated: ${new Date(document.updated_at).toLocaleString()}`}
          </p>
          {document.source && (
            <p className="text-sm text-muted-foreground mt-1">Source: {document.source}</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
