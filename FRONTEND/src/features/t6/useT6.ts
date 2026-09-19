import { useEffect, useRef, useState } from 'react';
import { ApiError, apiRequest } from '@/services/apiClient';
import { env } from '@/config/env';
import { emptyDelivery, parseEvidence } from './evidence';
import releaseManifest from './releaseManifest.json';
import type { Audit, DeliveryData, FinalRun, ReleaseState } from './types';

const STORAGE = 'aurora.final-delivery.v1';
export function useT6() {
  const [initial] = useState(() => {
    try { const saved = localStorage.getItem(STORAGE); return { data: saved ? parseEvidence(saved, releaseManifest.release_id) : emptyDelivery(releaseManifest.release_id), error: '' }; }
    catch { return { data: emptyDelivery(releaseManifest.release_id), error: 'O rascunho local não pôde ser carregado e foi preservado. Exporte uma cópia pelo armazenamento do navegador antes de editar; uma edição inicia um novo rascunho.' }; }
  });
  const [data, setData] = useState<DeliveryData>(initial.data);
  const [state, setState] = useState<ReleaseState | null>(null);
  const [audit, setAudit] = useState<Audit | null>(null);
  const [auditedData, setAuditedData] = useState<DeliveryData | null>(null);
  const [error, setError] = useState('');
  const [storageError, setStorageError] = useState(initial.error);
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState('');
  const controller = useRef<AbortController | null>(null);
  const stop = useRef(false);
  const mounted = useRef(true);
  const ready = Boolean(state?.frozen && state.manifest?.release_id === releaseManifest.release_id);
  useEffect(() => {
    mounted.current = true;
    const request = new AbortController();
    void apiRequest<ReleaseState>('/t6/manifest', { signal: request.signal }).then(setState).catch(() => { if (!request.signal.aborted) setError('Não foi possível consultar a versão final. Publique o backend com /t6 e o manifesto correspondente.'); });
    return () => { mounted.current = false; request.abort(); stop.current = true; controller.current?.abort(); };
  }, []);
  useEffect(() => {
    if (initial.error && data === initial.data) return;
    const timer = setTimeout(() => {
      try { localStorage.setItem(STORAGE, JSON.stringify(data)); setStorageError(''); }
      catch { setStorageError('O navegador não conseguiu salvar o histórico. Exporte o JSON antes de sair.'); }
    }, 150);
    return () => clearTimeout(timer);
  }, [data, initial]);
  useEffect(() => {
    if (!state?.manifest) return;
    const request = new AbortController();
    const timer = setTimeout(() => {
      void apiRequest<Audit>('/t6/audit', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data), signal: request.signal }).then(result => { if (!request.signal.aborted) { setAudit(result); setAuditedData(data); } }).catch(reason => { if (!request.signal.aborted) { setAudit(null); setError(reason instanceof ApiError ? reason.message : 'Falha ao validar as evidências. Nenhuma aprovação foi registrada.'); } });
    }, 300);
    return () => { clearTimeout(timer); request.abort(); };
  }, [data, state]);

  async function execute(items: { case_id: string; scene_id?: string }[], purpose: 'evaluation' | 'smoke') {
    if (controller.current || !ready || data.runs.length + items.length > 200) return;
    const request = new AbortController(); controller.current = request; stop.current = false;
    setBusy(true); setError('');
    try {
      for (const [index, item] of items.entries()) {
        if (stop.current) break;
        setProgress(`${index + 1}/${items.length} · ${item.scene_id ?? item.case_id}`);
        const timeout = setTimeout(() => request.abort(), 510_000);
        try {
          const run = await apiRequest<FinalRun>('/t6/run', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ...item, purpose, release_id: releaseManifest.release_id }), signal: request.signal });
          if (mounted.current) setData(previous => ({ ...previous, runs: [...previous.runs, run], decision: { ...previous.decision, choice: 'pendente' } }));
        } finally { clearTimeout(timeout); }
      }
    } catch (reason) { if (mounted.current) setError(reason instanceof ApiError ? reason.message : 'A execução não retornou evidência. O histórico recebido foi preservado; verifique o serviço antes de repetir.'); }
    finally { controller.current = null; if (mounted.current) { setBusy(false); setProgress(''); } }
  }
  async function download(kind: 'package' | 'presentation') {
    if (!ready || busy) return;
    setError('');
    try {
      const response = await fetch(`${env.apiUrl}/t6/${kind}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
      if (!response.ok) { const body = await response.json(); throw new Error(body.detail?.message ?? 'Falha ao gerar o arquivo.'); }
      const blob = await response.blob(); const url = URL.createObjectURL(blob); const anchor = document.createElement('a');
      anchor.href = url; anchor.download = response.headers.get('Content-Disposition')?.match(/filename="([^"]+)"/)?.[1] ?? (kind === 'package' ? `${audit?.recorded ? 'entrega' : 'rascunho'}-${releaseManifest.release_id}.zip` : 'apresentacao.pdf'); document.body.append(anchor); anchor.click(); anchor.remove(); setTimeout(() => URL.revokeObjectURL(url), 30_000);
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Não foi possível gerar o pacote.'); }
  }
  return { data, setData, state, audit: auditedData === data ? audit : null, error, storageError, ready, busy, progress, execute, stop: () => { stop.current = true; setProgress('Parando após a execução atual…'); }, download, frontendRelease: releaseManifest.release_id };
}
