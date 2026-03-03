'use client';

import { useSessionStore } from '@/lib/store';
import { Toaster } from '@/components/ui/sonner';
import { useEffect, useState, useRef } from 'react';
import { getCurrentUser, getWizardStatus } from '@/lib/api';
import { useRouter, usePathname } from 'next/navigation';
import type { WizardStatus } from '@/types/api';

export function Providers({ children }: { children: React.ReactNode }) {
  const { setUser, setLoading } = useSessionStore();
  const router = useRouter();
  const pathname = usePathname();
  const [isReady, setIsReady] = useState(false);
  const checkedRef = useRef<string | null>(null);

  useEffect(() => {
    if (checkedRef.current === pathname) return;
    checkedRef.current = pathname;

    let cancelled = false;

    async function checkWizardAndAuth() {
      if (cancelled) return;
      
      const status: WizardStatus = await getWizardStatus();
      
      if (cancelled) return;
      
      const isWizardPage = pathname === '/wizard';
      
      if (status.state !== 'completed' && !isWizardPage) {
        router.push('/wizard');
        return;
      }
      
      if (status.state === 'completed' && isWizardPage) {
        router.push('/login');
        return;
      }
      
      if (status.state !== 'completed') {
        setLoading(false);
        setIsReady(true);
        return;
      }

      const isAuthPage = pathname === '/login' || pathname === '/register';
      if (isAuthPage) {
        setLoading(false);
        setIsReady(true);
        return;
      }
      
      try {
        const user = await getCurrentUser();
        if (!cancelled) setUser(user);
      } catch {
        if (!cancelled) setUser(null);
      } finally {
        if (!cancelled) {
          setLoading(false);
          setIsReady(true);
        }
      }
    }
    
    checkWizardAndAuth();
    
    return () => { cancelled = true; };
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
