import { useCallback, useEffect, useRef, useState } from 'react';

import { getHealth } from '@/features/health/api/healthApi';
import type { ApiAvailability } from '@/types';

interface UseApiHealthResult {
  status: ApiAvailability;
  checkAgain: () => void;
}

/** Observa a saúde da API e permite uma nova tentativa manual. */
export function useApiHealth(): UseApiHealthResult {
  const [status, setStatus] = useState<ApiAvailability>('checking');
  const controllerRef = useRef<AbortController | null>(null);

  const checkHealth = useCallback((controller: AbortController): void => {
    void getHealth(controller.signal)
      .then(() => setStatus('online'))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === 'AbortError') {
          return;
        }
        setStatus('offline');
      });
  }, []);

  const checkAgain = useCallback((): void => {
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;
    setStatus('checking');
    checkHealth(controller);
  }, [checkHealth]);

  useEffect(() => {
    const controller = new AbortController();
    controllerRef.current = controller;
    checkHealth(controller);
    return () => controllerRef.current?.abort();
  }, [checkHealth]);

  return { status, checkAgain };
}
