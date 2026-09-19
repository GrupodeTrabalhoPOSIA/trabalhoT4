import { useEffect, useRef, useState } from 'react';
import { ApiError, apiRequest } from '@/services/apiClient';
import { PROJECT_MODEL_ID } from '@/common/modelPolicy';
import { candidate } from './data';
import type { Case, Config, Result, Review, Run } from './types';

export function useT5() {
  const [config, setConfig] = useState<Config | null>(null);
  const [configError, setConfigError] = useState(false);
  const [runs, setRuns] = useState<Run[]>([]);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const controller = useRef<AbortController | null>(null);
  useEffect(() => {
    const request = new AbortController();
    void apiRequest<Config>('/t5/config', { signal: request.signal }).then(setConfig).catch(() => { if (!request.signal.aborted) setConfigError(true); });
    return () => { request.abort(); controller.current?.abort(); };
  }, []);
  useEffect(() => {
    if (!runs.length) return;
    const warn = (event: BeforeUnloadEvent) => { event.preventDefault(); event.returnValue = ''; };
    window.addEventListener('beforeunload', warn);
    return () => window.removeEventListener('beforeunload', warn);
  }, [runs.length]);

  async function execute(question: string, file: File | null, selectedCase?: Case) {
    if (controller.current || !question.trim()) return;
    if (config?.candidate !== candidate || config?.model !== PROJECT_MODEL_ID) {
      setError('A API precisa confirmar a candidata t5-v1 e o Mistral Large. Atualize o backend e recarregue a página.'); return;
    }
    const request = new AbortController(); controller.current = request;
    setBusy(true); setError('');
    const timeout = setTimeout(() => request.abort(), 510_000);
    try {
      const data = new FormData(); data.set('question', question.trim()); data.set('mode', selectedCase?.mode ?? 'real');
      if (file) data.set('file', file);
      const result = await apiRequest<Result>('/t5/run', { method: 'POST', body: data, signal: request.signal });
      const run: Run = { ...result, case_id: selectedCase?.id ?? 'LIVRE', input_file: file?.name ?? null, expected: selectedCase?.expected ?? 'Execução exploratória; não integra as métricas dos 20 casos.', success: null, critical: null };
      setRuns(previous => [...previous, run]);
      return run.execution_id;
    } catch (reason) {
      if (!request.signal.aborted) setError(reason instanceof ApiError ? reason.message : 'Não foi possível acessar o Trabalho 5. Confira a conexão e o deploy do backend.');
      else setError('Tempo de espera excedido. Nenhum resultado foi recebido; confira o serviço antes de repetir.');
    } finally { clearTimeout(timeout); controller.current = null; setBusy(false); }
  }
  function assess(id: string, field: 'success' | 'critical', value: boolean | null) {
    setRuns(previous => previous.map(r => r.execution_id === id ? { ...r, [field]: value } : r));
  }
  return { config, configError, runs, reviews, setReviews, busy, error, execute, assess };
}
