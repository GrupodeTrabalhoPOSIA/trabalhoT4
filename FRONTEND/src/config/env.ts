const DEFAULT_API_URL = 'http://localhost:8000/api/v1';

/** Configuração pública e segura disponível no bundle do frontend. */
export const env = {
  apiUrl: import.meta.env.VITE_API_URL?.replace(/\/$/, '') || DEFAULT_API_URL,
} as const;

