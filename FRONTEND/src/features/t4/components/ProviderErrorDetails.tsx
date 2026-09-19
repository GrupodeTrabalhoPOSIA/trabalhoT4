import type { FlowAttempt } from '../utils/types';

const sourceLabels = {
  openrouter: 'OpenRouter',
  provider: 'Provedor do modelo',
  unknown: 'Não identificada pelo retorno recebido',
};

export default function ProviderErrorDetails({ attempt }: { attempt: FlowAttempt }) {
  const diagnostic = attempt.diagnostic;
  if (!diagnostic) return null;

  return <aside className="t4-notice" aria-label="Diagnóstico seguro do serviço">
    <strong>HTTP {diagnostic.http_status} · Diagnóstico do serviço</strong>
    <p>{diagnostic.message}</p>
    <p>Origem: {sourceLabels[diagnostic.source] ?? sourceLabels.unknown}.</p>
    {diagnostic.retry_after_seconds !== undefined
      ? <p>Espera solicitada pelo serviço: {diagnostic.retry_after_seconds} s.</p>
      : diagnostic.http_status === 429 && <p>O serviço não informou um prazo de espera válido.</p>}
    {attempt.retry_wait_seconds !== undefined && <p>Espera aplicada antes da repetição: {attempt.retry_wait_seconds} s.</p>}
    <small>Diagnóstico normalizado; mensagens brutas do provedor e credenciais não são expostas.</small>
  </aside>;
}
