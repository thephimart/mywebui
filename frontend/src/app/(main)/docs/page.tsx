'use client';

import { useState, useEffect } from 'react';
import { listDocuments, deleteDocument, ingestDocument } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useRouter } from 'next/navigation';
import { useCapabilities } from '@/hooks/useCapabilities';
import { FeatureUnavailable } from '@/components/FeatureUnavailable';
import type { Document } from '@/types/api';

export default function DocumentsPage() {
  const router = useRouter();
  const { capabilities } = useCapabilities();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newDoc, setNewDoc] = useState({ title: '', content: '', visibility: 'private' as 'private' | 'public' });

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    setIsLoading(true);
    try {
      const res = await listDocuments();
      setDocuments(res.documents);
    } catch (err) {
      console.error('Failed to load documents:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreate = async () => {
    try {
      await ingestDocument({
        title: newDoc.title,
        content: newDoc.content,
        visibility: newDoc.visibility,
        categories: [],
        source: null,
      });
      setIsCreateOpen(false);
      setNewDoc({ title: '', content: '', visibility: 'private' });
      loadDocuments();
    } catch (err) {
      console.error('Failed to create document:', err);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this document?')) return;
    try {
      await deleteDocument(id);
      loadDocuments();
    } catch (err) {
      console.error('Failed to delete document:', err);
    }
  };

  if (!capabilities?.filesystem?.enabled && !capabilities?.web?.enabled) {
    return <FeatureUnavailable feature="Documents" message="No storage capabilities available." />;
  }

  return (
    <div className="container mx-auto py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">Documents</h1>
        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogTrigger asChild>
            <Button>Add Document</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Document</DialogTitle>
              <DialogDescription>Add a new document to your knowledge base.</DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <Input
                placeholder="Document title"
                value={newDoc.title}
                onChange={(e) => setNewDoc({ ...newDoc, title: e.target.value })}
              />
              <Textarea
                placeholder="Document content"
                value={newDoc.content}
                onChange={(e) => setNewDoc({ ...newDoc, content: e.target.value })}
                rows={10}
              />
              <Select
                value={newDoc.visibility}
                onValueChange={(v) => setNewDoc({ ...newDoc, visibility: v as 'private' | 'public' })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Visibility" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="private">Private</SelectItem>
                  <SelectItem value="public">Public</SelectItem>
                </SelectContent>
              </Select>
              <Button onClick={handleCreate} className="w-full">
                Create Document
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {isLoading ? (
        <div className="text-center py-8">Loading...</div>
      ) : documents.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground">
          No documents yet. Create one to get started.
        </div>
      ) : (
        <div className="grid gap-4">
          {documents.map((doc) => (
            <Card key={doc.id} className="cursor-pointer hover:bg-gray-50" onClick={() => router.push(`/docs/${doc.id}`)}>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">{doc.title}</CardTitle>
                  <div className="flex gap-2" onClick={(e) => e.stopPropagation()}>
                    <Badge variant="outline">{doc.visibility}</Badge>
                    <Button variant="destructive" size="sm" onClick={() => handleDelete(doc.id)}>
                      Delete
                    </Button>
                  </div>
                </div>
                <CardDescription>
                  Created {new Date(doc.created_at).toLocaleDateString()}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  {doc.categories.length > 0 ? doc.categories.join(', ') : 'No categories'}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
