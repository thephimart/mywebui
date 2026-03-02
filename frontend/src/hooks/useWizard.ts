import { useEffect, useState } from 'react';
import { getWizardStatus } from '@/lib/api';
import type { WizardStatus } from '@/types/api';

export function useWizard() {
  const [status, setStatus] = useState<WizardStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    getWizardStatus()
      .then(setStatus)
      .catch(() => setStatus(null))
      .finally(() => setIsLoading(false));
  }, []);

  return { status, isLoading };
}
