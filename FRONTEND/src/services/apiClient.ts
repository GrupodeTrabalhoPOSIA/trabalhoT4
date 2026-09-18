import { env } from '@/config/env';
import type { ApiErrorResponse } from '@/types';

interface RequestOptions extends RequestInit {
  signal?: AbortSignal;
}

/** Erro conhecido retornado pelo backend. */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(message: string, status: number, code = 'API_ERROR') {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }
}

async function parseError(response: Response): Promise<ApiError> {
  try {
    const body = (await response.json()) as ApiErrorResponse;
    return new ApiError(body.detail.message, response.status, body.detail.code);
  } catch {
    return new ApiError('Não foi possível concluir a solicitação.', response.status);
  }
}

/** Executa uma requisição tipada para a API FastAPI. */
export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(`${env.apiUrl}${path}`, {
    ...options,
    headers: {
      Accept: 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    throw await parseError(response);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
