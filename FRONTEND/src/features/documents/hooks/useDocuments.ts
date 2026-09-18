import { useCallback, useEffect, useRef, useState } from 'react';

import {
  deleteDocument,
  listDocuments,
  uploadDocument,
} from '@/features/documents/api/documentApi';
import type {
  DocumentFeedback,
  KnowledgeDocument,
} from '@/features/documents/types/document';
import { ApiError } from '@/services';

interface UseDocumentsResult {
  documents: KnowledgeDocument[];
  isLoading: boolean;
  isUploading: boolean;
  deletingId: string | null;
  feedback: DocumentFeedback | null;
  reload: () => void;
  upload: (file: File) => Promise<boolean>;
  remove: (document: KnowledgeDocument) => Promise<void>;
  dismissFeedback: () => void;
}

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }
  return 'Não foi possível acessar a base de conhecimento.';
}

/** Centraliza o estado e as mutações da base de conhecimento real. */
export function useDocuments(): UseDocumentsResult {
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<DocumentFeedback | null>(null);
  const controllerRef = useRef<AbortController | null>(null);

  const loadDocuments = useCallback((controller: AbortController): void => {
    void listDocuments(controller.signal)
      .then((items) => {
        setDocuments(items);
        setFeedback(null);
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === 'AbortError') {
          return;
        }
        setFeedback({ kind: 'error', message: errorMessage(error) });
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      });
  }, []);

  const reload = useCallback((): void => {
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;
    setIsLoading(true);
    loadDocuments(controller);
  }, [loadDocuments]);

  useEffect(() => {
    const controller = new AbortController();
    controllerRef.current = controller;
    loadDocuments(controller);
    return () => controllerRef.current?.abort();
  }, [loadDocuments]);

  const upload = useCallback(async (file: File): Promise<boolean> => {
    setIsUploading(true);
    setFeedback(null);
    try {
      const document = await uploadDocument(file);
      setDocuments((current) => [document, ...current]);
      setFeedback({ kind: 'success', message: `${document.name} foi indexado com sucesso.` });
      return true;
    } catch (error: unknown) {
      setFeedback({ kind: 'error', message: errorMessage(error) });
      return false;
    } finally {
      setIsUploading(false);
    }
  }, []);

  const remove = useCallback(async (document: KnowledgeDocument): Promise<void> => {
    setDeletingId(document.id);
    setFeedback(null);
    try {
      await deleteDocument(document.id);
      setDocuments((current) => current.filter((item) => item.id !== document.id));
      setFeedback({ kind: 'success', message: `${document.name} foi removido.` });
    } catch (error: unknown) {
      setFeedback({ kind: 'error', message: errorMessage(error) });
    } finally {
      setDeletingId(null);
    }
  }, []);

  const dismissFeedback = useCallback((): void => setFeedback(null), []);

  return {
    documents,
    isLoading,
    isUploading,
    deletingId,
    feedback,
    reload,
    upload,
    remove,
    dismissFeedback,
  };
}
