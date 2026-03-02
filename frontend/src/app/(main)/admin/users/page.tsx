'use client';

import { useEffect, useState } from 'react';
import { listUsers, deleteUser, updateUser } from '@/lib/api';
import { useSessionStore } from '@/lib/store';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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
import { FeatureUnavailable } from '@/components/FeatureUnavailable';
import type { User } from '@/types/api';

export default function AdminUsersPage() {
  const { user } = useSessionStore();
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [editUser, setEditUser] = useState<User | null>(null);
  const [editRole, setEditRole] = useState<'admin' | 'user'>('user');
  const [editActive, setEditActive] = useState(true);

  useEffect(() => {
    if (!user || user.role !== 'admin') {
      return;
    }
    loadUsers();
  }, [user]);

  const loadUsers = async () => {
    setIsLoading(true);
    try {
      const data = await listUsers();
      setUsers(data);
    } catch (err) {
      console.error('Failed to load users:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdate = async () => {
    if (!editUser) return;
    try {
      await updateUser(editUser.id, {
        username: null,
        password: null,
        role: editRole,
        is_active: editActive,
      });
      setEditUser(null);
      loadUsers();
    } catch (err) {
      console.error('Failed to update user:', err);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this user?')) return;
    try {
      await deleteUser(id);
      loadUsers();
    } catch (err) {
      console.error('Failed to delete user:', err);
    }
  };

  // Gate: Render-time check to prevent data leak
  if (!user || user.role !== 'admin') {
    return <FeatureUnavailable feature="User Management" message="Admin access required." />;
  }

  return (
    <div className="container mx-auto py-8">
      <h1 className="text-2xl font-semibold mb-6">User Management</h1>

      {isLoading ? (
        <div className="text-center py-8">Loading...</div>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Users</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {users.map((u) => (
                <div key={u.id} className="flex items-center justify-between p-4 border rounded-lg">
                  <div>
                    <div className="font-medium">{u.username}</div>
                    <div className="text-sm text-muted-foreground">
                      Created {new Date(u.created_at).toLocaleDateString()}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Badge variant={u.role === 'admin' ? 'default' : 'secondary'}>
                      {u.role}
                    </Badge>
                    <Badge variant={u.is_active ? 'outline' : 'destructive'}>
                      {u.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                    <Dialog open={!!editUser} onOpenChange={(open) => !open && setEditUser(null)}>
                      <DialogTrigger asChild>
                        <Button variant="outline" size="sm" onClick={() => {
                          setEditUser(u);
                          setEditRole(u.role);
                          setEditActive(u.is_active);
                        }}>
                          Edit
                        </Button>
                      </DialogTrigger>
                      <DialogContent>
                        <DialogHeader>
                          <DialogTitle>Edit User</DialogTitle>
                          <DialogDescription>Update user permissions.</DialogDescription>
                        </DialogHeader>
                        <div className="space-y-4">
                          <div>
                            <label className="text-sm font-medium">Role</label>
                            <Select value={editRole} onValueChange={(v) => setEditRole(v as 'admin' | 'user')}>
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="admin">Admin</SelectItem>
                                <SelectItem value="user">User</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                          <div>
                            <label className="text-sm font-medium">Status</label>
                            <Select value={editActive ? 'active' : 'inactive'} onValueChange={(v) => setEditActive(v === 'active')}>
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="active">Active</SelectItem>
                                <SelectItem value="inactive">Inactive</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                          <Button onClick={handleUpdate} className="w-full">Save Changes</Button>
                        </div>
                      </DialogContent>
                    </Dialog>
                    <Button variant="destructive" size="sm" onClick={() => handleDelete(u.id)}>
                      Delete
                    </Button>
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
