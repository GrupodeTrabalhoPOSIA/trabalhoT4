interface ChatErrorProps {
  message: string;
  onRetry?: () => void;
}

function ChatError({ message, onRetry }: ChatErrorProps) {
  return (
    <div className="chat-error" role="alert">
      <span>{message}</span>
      {onRetry ? (
        <button type="button" onClick={onRetry}>
          Tentar novamente
        </button>
      ) : null}
    </div>
  );
}

export default ChatError;

