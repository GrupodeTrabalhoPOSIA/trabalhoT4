import type { PropsWithChildren } from 'react';

import { ApiStatus, useApiHealth } from '@/features/health';
import type { AppPage } from '@/types';

interface AppShellProps extends PropsWithChildren {
  activePage: AppPage;
  onNavigate: (page: AppPage) => void;
}

function AppShell({ children, activePage, onNavigate }: AppShellProps) {
  const { status, checkAgain } = useApiHealth();

  return (
    <div className="app-shell">
      <header className="app-header">
        <button
          className="brand"
          type="button"
          aria-label="Abrir o chat da Aurora Tech"
          onClick={() => onNavigate('chat')}
        >
          <span className="brand__mark" aria-hidden="true">
            A
          </span>
          <span className="brand__text">
            <strong>Aurora Tech</strong>
            <small>Assistente virtual</small>
          </span>
        </button>

        <div className="header-actions">
          <ApiStatus status={status} onRetry={checkAgain} />
          <nav className="main-navigation" aria-label="Navegação principal">
            <button
              className={activePage === 'chat' ? 'nav-button nav-button--active' : 'nav-button'}
              type="button"
              aria-current={activePage === 'chat' ? 'page' : undefined}
              onClick={() => onNavigate('chat')}
            >
              Chat
            </button>
            <button
              className={
                activePage === 'knowledge' ? 'nav-button nav-button--active' : 'nav-button'
              }
              type="button"
              aria-current={activePage === 'knowledge' ? 'page' : undefined}
              onClick={() => onNavigate('knowledge')}
            >
              Base de conhecimento
            </button>
          </nav>
        </div>
      </header>

      <main className="app-content">{children}</main>
    </div>
  );
}

export default AppShell;
