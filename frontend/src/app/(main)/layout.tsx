'use client';

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useSessionStore } from '@/lib/store';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';

export default function MainLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isAuthenticated, isLoading } = useSessionStore();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push(`/login?redirect=${pathname}`);
    }
  }, [isLoading, isAuthenticated, router, pathname]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  const navItems = [
    { href: '/chat', label: 'Chat' },
    { href: '/docs', label: 'Documents' },
    { href: '/docs/search', label: 'Search' },
  ];

  if (user?.role === 'admin') {
    navItems.push({ href: '/admin', label: 'Admin' });
  }

  navItems.push({ href: '/settings', label: 'Settings' });

  return (
    <div className="flex h-screen">
      <aside className="w-56 border-r bg-gray-50">
        <div className="p-4 border-b">
          <h1 className="text-xl font-semibold">MyWebUI</h1>
          <p className="text-sm text-muted-foreground">{user?.username}</p>
        </div>
        <ScrollArea className="h-[calc(100vh-73px)]">
          <div className="p-2 space-y-1">
            {navItems.map((item) => (
              <Button
                key={item.href}
                variant={pathname === item.href ? 'secondary' : 'ghost'}
                className="w-full justify-start"
                onClick={() => router.push(item.href)}
              >
                {item.label}
              </Button>
            ))}
          </div>
        </ScrollArea>
      </aside>
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
}
