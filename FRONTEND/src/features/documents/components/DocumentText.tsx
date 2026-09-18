import { useEffect, useState } from 'react';

import { getDocumentContent } from '@/features/documents/api/documentApi';
import type { DocumentContentResponse } from '@/features/documents/types/document';

interface DocumentTextProps {
  documentId: string;
  name: string;
}

function DocumentText({ documentId, name }: DocumentTextProps) {
  const [content, setContent] = useState<DocumentContentResponse | null>(null);
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    getDocumentContent(documentId, controller.signal)
      .then((result) => {
        if (!controller.signal.aborted) setContent(result);
      })
      .catch(() => {
        if (!controller.signal.aborted) setFailed(true);
      });
    return () => controller.abort();
  }, [documentId, attempt]);

  return (
    <section className="document-text" aria-label={`Texto de ${name}`}>
      <h3>Texto indexado</h3>
      {failed ? (
        <div role="alert">
          <p>Não foi possível carregar o texto deste documento.</p>
          <button
            type="button"
            className="secondary-button"
            onClick={() => {
              setFailed(false);
              setAttempt((value) => value + 1);
            }}
          >
            Tentar carregar o texto novamente
          </button>
        </div>
      ) : content === null ? (
        <p role="status">Carregando texto…</p>
      ) : content.chunks.length === 0 ? (
        <p>Nenhum texto disponível para este documento.</p>
      ) : (
        <>
          {content.chunks.length > 1 && (
            <p>Trechos na ordem de leitura; partes podem se repetir entre eles.</p>
          )}
          {content.chunks.map((chunk) => (
            <div className="document-text__chunk" key={chunk.chunk_index}>
              {content.chunks.length > 1 && <h4>Trecho {chunk.chunk_index + 1}</h4>}
              <p className="document-text__body">{chunk.content}</p>
            </div>
          ))}
        </>
      )}
    </section>
  );
}

export default DocumentText;
