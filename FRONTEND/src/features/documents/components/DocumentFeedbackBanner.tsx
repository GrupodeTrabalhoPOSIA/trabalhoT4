import type { DocumentFeedback } from '@/features/documents/types/document';

interface DocumentFeedbackBannerProps {
  feedback: DocumentFeedback;
  onDismiss: () => void;
}

function DocumentFeedbackBanner({ feedback, onDismiss }: DocumentFeedbackBannerProps) {
  return (
    <div className={`document-feedback document-feedback--${feedback.kind}`} role="status">
      <span>{feedback.message}</span>
      <button type="button" aria-label="Fechar mensagem" onClick={onDismiss}>
        ×
      </button>
    </div>
  );
}

export default DocumentFeedbackBanner;

