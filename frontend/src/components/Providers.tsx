'use client';

import { useSessionStore } from '@/lib/store';
import { Toaster } from '@/components/ui/sonner';
import { useEffect, useState } from 'react';
import { getCurrentUser, getWizardStatus } from '@/lib/api';
import { useRouter, usePathname } from 'next/navigation';
import type { WizardStatus } from '@/types/api';

export function Providers({ children }: { children: React.ReactNode }) {
  const { setUser, setLoading } = useSessionStore();
  const router = useRouter();
  const pathname = usePathname();
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    async function checkWizardAndAuth() {
      try {
        const status: WizardStatus = await getWizardStatus();
        
        const isWizardPage = pathname === '/wizard';
        
        if (status.state !== 'completed' && !isWizardPage) {
          router.push('/wizard');
          return;
        }
        
        if (status.state === 'completed' && isWizardPage) {
          router.push('/chat');
          return;
        }
        
        const user = await getCurrentUser();
        setUser(user);
      } catch {
        setUser(null);
      } finally {
        setLoading(false);
        setIsReady(true);
      }
    }
    
    checkWizardAndAuth();
  }, [pathname, router, setUser, setLoading]);

  if (!isReady) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900" />
      </div>
    );
  }

  return (
    <>
      {children}
      <Toaster />
    </>
  );
}
