import { apiRequest } from '@/services/apiClient';
import type { FlowConfig, FlowRequest, FlowResult } from '../utils/types';

export function getFlowConfig(signal?: AbortSignal): Promise<FlowConfig> {
  return apiRequest('/t4/config', { signal });
}

export function runFlow(request: FlowRequest, signal?: AbortSignal): Promise<FlowResult> {
  return apiRequest('/t4/run', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request), signal,
  });
}
