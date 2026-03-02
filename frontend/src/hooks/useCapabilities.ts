import { useEffect, useState } from 'react';
import { getCapabilities } from '@/lib/api';
import type { Capabilities } from '@/types/api';

export function useCapabilities() {
  const [capabilities, setCapabilities] = useState<Capabilities['capabilities'] | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    getCapabilities()
      .then((res) => setCapabilities(res.capabilities))
      .catch(() => setCapabilities(null))
      .finally(() => setIsLoading(false));
  }, []);

  return { capabilities, isLoading };
}
