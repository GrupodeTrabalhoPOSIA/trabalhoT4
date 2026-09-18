import { useCallback, useEffect, useRef } from 'react';

const acceptedFormats = '.pdf,.txt,.md,.docx';

interface DocumentUploadProps {
  selectedFile: File | null;
  isUploading: boolean;
  onSelect: (file: File | null) => void;
  onUpload: () => void;
}

function DocumentUpload({
  selectedFile,
  isUploading,
  onSelect,
  onUpload,
}: DocumentUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!selectedFile && inputRef.current) {
      inputRef.current.value = '';
    }
  }, [selectedFile]);

  const handleInputChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>): void => {
      onSelect(event.target.files?.[0] ?? null);
    },
    [onSelect],
  );

  const handleOpenPicker = useCallback((): void => {
    inputRef.current?.click();
  }, []);

  return (
    <div className="document-upload">
      <input
        ref={inputRef}
        className="sr-only"
        type="file"
        accept={acceptedFormats}
        aria-label="Selecionar documento para a base de conhecimento"
        onChange={handleInputChange}
      />
      <button
        className="document-picker"
        type="button"
        aria-label={selectedFile ? `Trocar o arquivo ${selectedFile.name}` : 'Selecionar documento'}
        onClick={handleOpenPicker}
      >
        <span className="document-picker__icon" aria-hidden="true">
          ↑
        </span>
        <span>
          <strong>{selectedFile ? selectedFile.name : 'Selecionar um documento'}</strong>
          <small>PDF, TXT, Markdown ou DOCX · até 10 MB</small>
        </span>
      </button>
      <button
        className="primary-button"
        type="button"
        disabled={!selectedFile || isUploading}
        onClick={onUpload}
      >
        {isUploading ? 'Processando…' : 'Adicionar à base'}
      </button>
    </div>
  );
}

export default DocumentUpload;
