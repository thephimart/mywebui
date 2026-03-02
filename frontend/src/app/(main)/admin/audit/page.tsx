'use client';

import { useEffect, useState } from 'react';
import { listAuditEvents } from '@/lib/api';
import { useSessionStore } from '@/lib/store';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { FeatureUnavailable } from '@/components/FeatureUnavailable';
import type { AuditEvent } from '@/types/api';

export default function AdminAuditPage() {
  const { user } = useSessionStore();
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    if (!user || user.role !== 'admin') {
      return;
    }
    loadEvents();
  }, [user]);

  const loadEvents = async () => {
    setIsLoading(true);
    try {
      const data = await listAuditEvents(0, 100);
      setEvents(data.events);
      setTotal(data.total);
    } catch (err) {
      console.error('Failed to load audit events:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Gate: Render-time check to prevent data leak
  if (!user || user.role !== 'admin') {
    return <FeatureUnavailable feature="Audit Logs" message="Admin access required." />;
  }

  return (
    <div className="container mx-auto py-8">
      <h1 className="text-2xl font-semibold mb-6">Audit Logs</h1>
      <p className="text-sm text-muted-foreground mb-6">Showing {events.length} of {total} events (read-only)</p>

      {isLoading ? (
        <div className="text-center py-8">Loading...</div>
      ) : events.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground">No audit events yet.</div>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Events</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {events.map((event) => (
                <div key={event.id} className="flex items-center justify-between p-3 border rounded-lg">
                  <div>
                    <div className="font-mono text-sm">{event.id.slice(0, 8)}...</div>
                    <div className="text-sm text-muted-foreground">
                      {new Date(event.timestamp).toLocaleString()}
                    </div>
                  </div>
                  <div className="flex gap-2 items-center">
                    <Badge variant="outline">{event.event_type}</Badge>
                    {event.user_id && (
                      <span className="text-xs text-muted-foreground">User: {event.user_id.slice(0, 8)}...</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
