import { useEffect } from 'react';
import { useSessionStore } from '@/lib/store';
import { getCurrentUser } from '@/lib/api';

export function useSession() {
  const { user, setUser, isAuthenticated, isLoading } = useSessionStore();

  useEffect(() => {
    if (!isAuthenticated && !isLoading) {
      getCurrentUser()
        .then(setUser)
        .catch(() => setUser(null));
    }
  }, [isAuthenticated, isLoading, setUser]);

  return { user, isAuthenticated, isLoading };
}
