function ChatLoading() {
  return (
    <div className="chat-loading" role="status" aria-live="polite">
      <span />
      <span />
      <span />
      <span className="sr-only">Aurora está preparando uma resposta</span>
    </div>
  );
}

export default ChatLoading;

