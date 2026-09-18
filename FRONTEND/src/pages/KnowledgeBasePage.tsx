import { useCallback, useState } from 'react';

import {
  DocumentFeedbackBanner,
  DocumentList,
  DocumentUpload,
  useDocuments,
} from '@/features/documents';

const acceptedExtensions = new Set(['pdf', 'txt', 'md', 'docx']);
const maxFileSize = 10 * 1024 * 1024;

function getExtension(filename: string): string {
  return filename.split('.').pop()?.toLowerCase() ?? '';
}

function KnowledgeBasePage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);
  const {
    documents,
    isLoading,
    isUploading,
    deletingId,
    feedback,
    reload,
    upload,
    remove,
    dismissFeedback,
  } = useDocuments();

  const handleSelect = useCallback((file: File | null): void => {
    setValidationError(null);
    dismissFeedback();
    if (!file) {
      setSelectedFile(null);
      return;
    }

    const extension = getExtension(file.name);
    if (!acceptedExtensions.has(extension)) {
      setSelectedFile(null);
      setValidationError('Formato inválido. Use PDF, TXT, MD ou DOCX.');
      return;
    }
    if (file.size > maxFileSize) {
      setSelectedFile(null);
      setValidationError('O arquivo deve ter no máximo 10 MB.');
      return;
    }
    setSelectedFile(file);
  }, [dismissFeedback]);

  const handleUpload = useCallback(async (): Promise<void> => {
    if (!selectedFile) {
      return;
    }

    const succeeded = await upload(selectedFile);
    if (succeeded) {
      setSelectedFile(null);
    }
  }, [selectedFile, upload]);

  const handleRemove = useCallback((document: (typeof documents)[number]): void => {
    const confirmed = window.confirm(`Remover "${document.name}" da base de conhecimento?`);
    if (!confirmed) {
      return;
    }
    void remove(document);
  }, [remove]);

  return (
    <section className="knowledge-page" aria-labelledby="knowledge-title">
      <div className="page-heading">
        <span className="eyebrow">Conteúdo do assistente</span>
        <h1 id="knowledge-title">Base de conhecimento</h1>
        <p>
          Aqui serão adicionados os documentos usados pelo chatbot para responder às
          perguntas sobre a Aurora Tech.
        </p>
      </div>

      <div className="knowledge-workspace">
        <DocumentUpload
          selectedFile={selectedFile}
          isUploading={isUploading}
          onSelect={handleSelect}
          onUpload={() => void handleUpload()}
        />
        {validationError ? (
          <DocumentFeedbackBanner
            feedback={{ kind: 'error', message: validationError }}
            onDismiss={() => setValidationError(null)}
          />
        ) : feedback ? (
          <DocumentFeedbackBanner feedback={feedback} onDismiss={dismissFeedback} />
        ) : null}
        <div className="document-list-heading">
          <div>
            <span className="eyebrow">Arquivos preparados</span>
            <h2>Documentos</h2>
          </div>
          <span className="document-count" aria-label={`${documents.length} documentos`}>
            {documents.length}
          </span>
        </div>
        {isLoading ? (
          <div className="documents-loading" role="status">
            Carregando documentos…
          </div>
        ) : feedback?.kind === 'error' && documents.length === 0 ? (
          <div className="documents-retry">
            <p>A lista não pôde ser carregada.</p>
            <button className="primary-button" type="button" onClick={reload}>
              Tentar novamente
            </button>
          </div>
        ) : (
          <DocumentList
            documents={documents}
            deletingId={deletingId}
            onRemove={handleRemove}
          />
        )}
      </div>
    </section>
  );
}

export default KnowledgeBasePage;
