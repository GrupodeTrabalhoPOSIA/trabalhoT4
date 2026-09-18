import { useState } from 'react';

interface ChatComposerProps {
  disabled?: boolean;
  isSending?: boolean;
  onSubmit: (message: string) => void;
}

function ChatComposer({ disabled = false, isSending = false, onSubmit }: ChatComposerProps) {
  const [message, setMessage] = useState('');

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!message.trim() || disabled || isSending) {
      return;
    }
    onSubmit(message);
    setMessage('');
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (
      event.key !== 'Enter' ||
      event.shiftKey ||
      event.nativeEvent.isComposing ||
      event.nativeEvent.keyCode === 229
    ) {
      return;
    }
    event.preventDefault();
    if (!event.repeat) {
      event.currentTarget.form?.requestSubmit();
    }
  }

  return (
    <form className="composer" aria-label="Enviar uma pergunta" onSubmit={handleSubmit}>
      <label className="sr-only" htmlFor="chat-message">
        Sua pergunta
      </label>
      <textarea
        id="chat-message"
        name="message"
        rows={1}
        placeholder="Digite sua pergunta…"
        disabled={disabled || isSending}
        maxLength={2000}
        value={message}
        onChange={(event) => setMessage(event.target.value)}
        onKeyDown={handleKeyDown}
        aria-describedby="chat-message-hint"
      />
      <span id="chat-message-hint" className="sr-only">
        Enter para enviar. Shift+Enter para uma nova linha.
      </span>
      <button type="submit" disabled={disabled || isSending || !message.trim()}>
        {isSending ? 'Enviando…' : 'Enviar'}
      </button>
    </form>
  );
}

export default ChatComposer;
