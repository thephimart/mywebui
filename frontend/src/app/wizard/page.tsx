'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getWizardStatus, createWizardAdmin, completeWizard } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function WizardPage() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [action, setAction] = useState<'reuse' | 'backup' | 'abort'>('reuse');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [wizardState, setWizardState] = useState<string | null>(null);

  useEffect(() => {
    getWizardStatus().then((status) => {
      setWizardState(status.state);
      if (status.state === 'completed') {
        router.push('/chat');
      }
    });
  }, [router]);

  const handleCreateAdmin = async () => {
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      await createWizardAdmin({ username, password });
      router.push('/chat');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create admin');
    } finally {
      setIsLoading(false);
    }
  };

  const handleComplete = async () => {
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      await completeWizard({ username, password, action });
      router.push('/chat');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to complete wizard');
    } finally {
      setIsLoading(false);
    }
  };

  if (wizardState === 'completed') {
    return null;
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Welcome to MyWebUI</CardTitle>
          <CardDescription>Complete the setup to get started</CardDescription>
        </CardHeader>
        <CardContent>
          {wizardState === 'needs_setup_with_existing_data' ? (
            <>
              <div className="space-y-4 mb-6">
                <p className="text-sm text-muted-foreground">
                  Existing data was detected. How would you like to proceed?
                </p>
                <div className="flex gap-2">
                  <Button
                    variant={action === 'reuse' ? 'default' : 'outline'}
                    onClick={() => setAction('reuse')}
                    className="flex-1"
                  >
                    Reuse
                  </Button>
                  <Button
                    variant={action === 'backup' ? 'default' : 'outline'}
                    onClick={() => setAction('backup')}
                    className="flex-1"
                  >
                    Backup
                  </Button>
                  <Button
                    variant={action === 'abort' ? 'destructive' : 'outline'}
                    onClick={() => setAction('abort')}
                    className="flex-1"
                  >
                    Abort
                  </Button>
                </div>
              </div>
              <div className="space-y-4">
                <Input
                  placeholder="Admin Username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                />
                <Input
                  type="password"
                  placeholder="Password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
                <Input
                  type="password"
                  placeholder="Confirm Password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                />
                {error && <p className="text-sm text-red-500">{error}</p>}
                <Button className="w-full" onClick={handleComplete} disabled={isLoading}>
                  {isLoading ? 'Setting up...' : 'Complete Setup'}
                </Button>
              </div>
            </>
          ) : (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground mb-4">
                Create an admin account to get started.
              </p>
              <Input
                placeholder="Admin Username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
              <Input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <Input
                type="password"
                placeholder="Confirm Password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
              />
              {error && <p className="text-sm text-red-500">{error}</p>}
              <Button className="w-full" onClick={handleCreateAdmin} disabled={isLoading}>
                {isLoading ? 'Creating...' : 'Create Admin'}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
