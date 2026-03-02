'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getWizardStatus } from '@/lib/api';
import type { WizardStatus } from '@/types/api';

export function WizardGate({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [status, setStatus] = useState<WizardStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    getWizardStatus()
      .then((data) => {
        setStatus(data);
        if (data.state !== 'completed') {
          router.push('/wizard');
        }
      })
      .catch(() => {
        // If we can't get wizard status, proceed (might be authenticated already)
      })
      .finally(() => setIsLoading(false));
  }, [router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900" />
      </div>
    );
  }

  if (status && status.state !== 'completed') {
    return null;
  }

  return <>{children}</>;
}
