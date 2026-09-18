import type { KnowledgeDocument } from '@/features/documents/types/document';
import DocumentText from './DocumentText';

interface DocumentListProps {
  documents: KnowledgeDocument[];
  deletingId?: string | null;
  onRemove: (document: KnowledgeDocument) => void;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  return `${(bytes / 1024).toFixed(1)} KB`;
}

function DocumentList({ documents, deletingId = null, onRemove }: DocumentListProps) {
  if (documents.length === 0) {
    return (
      <div className="empty-state empty-state--documents">
        <span className="empty-state__icon" aria-hidden="true">
          +
        </span>
        <h2>Nenhum documento adicionado</h2>
        <p>Escolha um arquivo acima para preparar a base do chatbot.</p>
      </div>
    );
  }

  return (
    <div className="document-list" aria-label="Documentos indexados">
      {documents.map((document) => (
        <article className="document-card" key={document.id}>
          <span className="document-card__type" aria-hidden="true">
            {document.type.toUpperCase()}
          </span>
          <div className="document-card__content">
            <h2>{document.name}</h2>
            <p>
              {document.chunkCount} {document.chunkCount === 1 ? 'trecho' : 'trechos'} ·{' '}
              {formatSize(document.size)}
            </p>
          </div>
          <button
            className="danger-button"
            type="button"
            disabled={deletingId === document.id}
            aria-label={`Remover ${document.name}`}
            onClick={() => onRemove(document)}
          >
            {deletingId === document.id ? 'Removendo…' : 'Remover'}
          </button>
          {document.type === 'txt' && (
            <DocumentText documentId={document.id} name={document.name} />
          )}
        </article>
      ))}
    </div>
  );
}

export default DocumentList;
