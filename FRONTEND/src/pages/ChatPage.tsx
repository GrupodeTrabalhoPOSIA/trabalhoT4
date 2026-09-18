import { ChatComposer, ChatError, ChatLoading, ChatMessage, useChat } from '@/features/chat';

function ChatPage() {
  const { messages, isSending, error, submit, retry, clear } = useChat();

  return (
    <section className="chat-page" aria-labelledby="chat-title">
      <div className="chat-welcome chat-welcome--compact">
        <span className="eyebrow">Conhecimento que conversa</span>
        <h1 id="chat-title">Olá! Sou o assistente da Aurora Tech.</h1>
        <p>
          Faça uma pergunta sobre a empresa. Minhas respostas serão baseadas nos
          documentos cadastrados na base de conhecimento.
        </p>

      </div>

      <div className="chat-toolbar">
        <span>{messages.length === 0 ? 'Nova conversa' : `${messages.length} mensagens`}</span>
        {messages.length > 0 ? (
          <button type="button" onClick={clear} disabled={isSending}>
            Limpar conversa
          </button>
        ) : null}
      </div>

      <div className="chat-thread" aria-label="Conversa" aria-live="polite">
        {messages.length === 0 ? (
          <div className="chat-empty">
            Pergunte sobre serviços, atendimento ou qualquer informação cadastrada.
          </div>
        ) : null}
        {messages.map((message) => (
          <ChatMessage message={message} key={message.id} />
        ))}
        {isSending ? <ChatLoading /> : null}
        {error ? <ChatError message={error} onRetry={retry} /> : null}
      </div>

      <ChatComposer isSending={isSending} onSubmit={(message) => void submit(message)} />
    </section>
  );
}

export default ChatPage;
