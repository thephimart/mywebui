'use client';

import { useEffect, useState } from 'react';
import { getSessions, deleteSession, deleteAllSessions } from '@/lib/api';
import { useSessionStore } from '@/lib/store';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import type { Session } from '@/types/api';

export default function SessionsPage() {
  const router = useRouter();
  const { setUser } = useSessionStore();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    setIsLoading(true);
    try {
      const data = await getSessions();
      setSessions(data.sessions);
    } catch (err) {
      console.error('Failed to load sessions:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRevoke = async (id: string) => {
    if (!confirm('Are you sure you want to revoke this session?')) return;
    try {
      await deleteSession(id);
      loadSessions();
    } catch (err) {
      console.error('Failed to revoke session:', err);
    }
  };

  const handleRevokeAll = async () => {
    if (!confirm('Are you sure you want to revoke all sessions? You will be signed out.')) return;
    try {
      await deleteAllSessions();
      setUser(null);
      router.push('/login');
    } catch (err) {
      console.error('Failed to revoke sessions:', err);
    }
  };

  return (
    <div className="container mx-auto py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">Active Sessions</h1>
        <Button variant="destructive" onClick={handleRevokeAll}>
          Revoke All Sessions
        </Button>
      </div>

      {isLoading ? (
        <div className="text-center py-8">Loading...</div>
      ) : sessions.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground">No active sessions.</div>
      ) : (
        <div className="space-y-4 max-w-2xl">
          {sessions.map((session) => (
            <Card key={session.session_id}>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base font-mono">
                    {session.session_id.slice(0, 8)}...
                  </CardTitle>
                  <Badge variant={session.revoked ? 'destructive' : 'outline'}>
                    {session.revoked ? 'Revoked' : 'Active'}
                  </Badge>
                </div>
                <CardDescription>
                  Issued: {new Date(session.issued_at).toLocaleString()}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between">
                  <div className="text-sm text-muted-foreground">
                    Expires: {new Date(session.expires_at).toLocaleString()}
                  </div>
                  {!session.revoked && (
                    <Button variant="outline" size="sm" onClick={() => handleRevoke(session.session_id)}>
                      Revoke
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
