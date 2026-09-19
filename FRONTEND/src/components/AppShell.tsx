import type { PropsWithChildren } from 'react';
import { PROJECT_MODEL_NAME, PROJECT_MODEL_URL } from '@/common/modelPolicy';

import { ApiStatus, useApiHealth } from '@/features/health';
import { pagePaths, pageTitles } from '@/features/deliveries/utils/catalogue';
import type { AppPage } from '@/types';

interface AppShellProps extends PropsWithChildren {
  activePage: AppPage;
}

function LiveApiStatus() {
  const { status, checkAgain } = useApiHealth();
  return <ApiStatus status={status} onRetry={checkAgain} />;
}

function AppShell({ children, activePage }: AppShellProps) {
  const interactive = ['t4', 't5', 't6', 'chat', 'knowledge'].includes(activePage);
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content" onClick={event => { event.preventDefault(); document.getElementById('main-content')?.focus(); }}>Pular para o conteúdo</a>
      <header className="app-header">
        <a
          className="brand"
          aria-label="Abrir portal das entregas da Aurora Tech"
          href={pagePaths.overview}
        >
          <span className="brand__mark" aria-hidden="true">
            A
          </span>
          <span className="brand__text">
            <strong>Aurora Tech</strong>
            <small>Copiloto de RH · Portfólio acadêmico</small>
          </span>
        </a>

        <div className="header-actions">
          <nav className="main-navigation" aria-label="Navegação principal">
            {(['overview', 't1', 't2', 't3', 't4', 't5', 't6'] as const).map(page => <a key={page} href={pagePaths[page]} aria-label={page === 'overview' ? 'Visão geral' : pageTitles[page]} className={activePage === page ? 'nav-button nav-button--active' : 'nav-button'} aria-current={activePage === page ? 'page' : undefined}>{page === 'overview' ? 'Visão geral' : <><span className="nav-full-label">Trabalho </span><span className="nav-short-label">T</span>{page.slice(1)}</>}</a>)}
            <a href={pagePaths.about} className={activePage === 'about' ? 'nav-button nav-button--active' : 'nav-button'} aria-current={activePage === 'about' ? 'page' : undefined}>Sobre</a>
          </nav>
        </div>
      </header>

      <div className="portal-utility-bar"><div className="portal-model-policy">Modelo do projeto: <a href={PROJECT_MODEL_URL} target="_blank" rel="noreferrer">{PROJECT_MODEL_NAME}</a><span> · escolha do Trabalho 1</span></div><nav aria-label="Recursos complementares"><span>Laboratório</span><a href={pagePaths.chat} aria-current={activePage === 'chat' ? 'page' : undefined}>{pageTitles.chat}</a><a href={pagePaths.knowledge} aria-current={activePage === 'knowledge' ? 'page' : undefined}>{pageTitles.knowledge}</a>{interactive && <LiveApiStatus />}</nav></div>
      <main id="main-content" className="app-content" tabIndex={-1}>{children}</main>
    </div>
  );
}

export default AppShell;
