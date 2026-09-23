import { useEffect, useState } from 'react';
import { getFlowConfig } from '@/features/t4/services/t4Api';

export function useConfiguredModel() {
  const [model, setModel] = useState<string | null>(null);
  useEffect(() => {
    const request = new AbortController();
    void getFlowConfig(request.signal).then(config => {
      if (!request.signal.aborted) setModel(config.model);
    }).catch(() => {});
    return () => request.abort();
  }, []);
  return model;
}
