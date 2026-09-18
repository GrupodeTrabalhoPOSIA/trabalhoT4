import { apiRequest } from '@/services';
import type { HealthResponse } from '@/types';

/** Consulta a disponibilidade básica do backend. */
export function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  return apiRequest<HealthResponse>('/health', { signal });
}

