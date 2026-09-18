import type { ApiAvailability } from '@/types';

interface ApiStatusProps {
  status: ApiAvailability;
  onRetry: () => void;
}

const statusLabels: Record<ApiAvailability, string> = {
  checking: 'Verificando API',
  online: 'API disponível',
  offline: 'API indisponível',
};

function ApiStatus({ status, onRetry }: ApiStatusProps) {
  const className = `api-status api-status--${status}`;

  return (
    <button
      className={className}
      type="button"
      aria-live="polite"
      title={status === 'offline' ? 'Tentar conectar novamente' : statusLabels[status]}
      onClick={status === 'offline' ? onRetry : undefined}
    >
      <span className="api-status__dot" aria-hidden="true" />
      {statusLabels[status]}
    </button>
  );
}

export default ApiStatus;

