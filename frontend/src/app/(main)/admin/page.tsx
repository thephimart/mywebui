'use client';

import { useRouter } from 'next/navigation';
import { useSessionStore } from '@/lib/store';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { FeatureUnavailable } from '@/components/FeatureUnavailable';

export default function AdminPage() {
  const router = useRouter();
  const { user } = useSessionStore();

  if (user?.role !== 'admin') {
    return <FeatureUnavailable feature="Admin Dashboard" message="Admin access required." />;
  }

  return (
    <div className="container mx-auto py-8">
      <h1 className="text-2xl font-semibold mb-6">Admin Dashboard</h1>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Users</CardTitle>
            <CardDescription>Manage user accounts and permissions</CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={() => router.push('/admin/users')}>Manage Users</Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Audit Logs</CardTitle>
            <CardDescription>View system audit events (read-only)</CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={() => router.push('/admin/audit')}>View Logs</Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Settings</CardTitle>
            <CardDescription>System configuration</CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={() => router.push('/admin/settings')}>Configure</Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
