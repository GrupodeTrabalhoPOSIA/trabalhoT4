import { useEffect, useRef, useState } from 'react';
import { ApiError } from '@/services/apiClient';
import { PROJECT_MODEL_ID } from '@/common/modelPolicy';
import { getFlowConfig, runFlow } from '../services/t4Api';
import type { Evidence, FlowConfig, ReviewField, TestCase } from '../utils/types';

export function useT4() {
  const [config, setConfig] = useState<FlowConfig | null>(null);
  const [configError, setConfigError] = useState(false);
  const [runs, setRuns] = useState<Evidence[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const controller = useRef<AbortController | null>(null);
  useEffect(() => {
    const request = new AbortController();
    void getFlowConfig(request.signal).then(setConfig).catch(() => {
      if (!request.signal.aborted) setConfigError(true);
    });
    return () => { request.abort(); controller.current?.abort(); };
  }, []);

  async function execute(question: string, correction: string, testCase?: TestCase) {
    if (controller.current) return;
    if ((testCase?.mode ?? 'real') === 'real' && config?.model !== PROJECT_MODEL_ID) {
      setError('Execução real bloqueada: o backend precisa confirmar mistralai/mistral-large, escolhido no Trabalho 1. Atualize o backend e recarregue a página.');
      return;
    }
    const request = new AbortController();
    controller.current = request;
    setBusy(true);
    setError('');
    setSelectedId(null);
    // Até três chamadas sequenciais (roteamento, especialista e uma repetição).
    const timeout = setTimeout(() => request.abort(), 390_000);
    try {
      const result = await runFlow({ question, correction, mode: testCase?.mode ?? 'real' }, request.signal);
      const evidence: Evidence = { ...result, case_id: testCase?.id ?? 'LIVRE', category: testCase?.category ?? 'livre', expected: testCase?.expected ?? '', review: { conclusion: null, format: null, factuality: null, refusal: null } };
      setRuns(previous => [...previous, evidence]);
      setSelectedId(result.execution_id);
    } catch (reason) {
      setError(reason instanceof ApiError ? reason.message : request.signal.aborted ? 'A execução excedeu o tempo de espera. Nenhum resultado foi registrado; confira os logs antes de repetir.' : 'Não foi possível acessar o fluxo T4. Confirme o deploy do backend e tente novamente.');
    } finally {
      clearTimeout(timeout);
      controller.current = null;
      setBusy(false);
    }
  }

  function review(id: string, field: ReviewField, value: boolean | null) {
    setRuns(previous => previous.map(r => r.execution_id === id ? { ...r, review: { ...r.review, [field]: value } } : r));
  }
  return { config, configError, runs, busy, error, execute, review, selectedId, setSelectedId, selected: runs.find(r => r.execution_id === selectedId) ?? null };
}
