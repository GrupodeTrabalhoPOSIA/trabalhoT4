import { lazy, Suspense, useCallback, useState } from 'react';

import AppShell from '@/components/AppShell';
import PageLoader from '@/components/PageLoader';
import type { AppPage } from '@/types';

const ChatPage = lazy(() => import('@/pages/ChatPage'));
const KnowledgeBasePage = lazy(() => import('@/pages/KnowledgeBasePage'));

function App() {
  const [activePage, setActivePage] = useState<AppPage>('chat');

  const handleNavigate = useCallback((page: AppPage): void => {
    setActivePage(page);
  }, []);

  return (
    <AppShell activePage={activePage} onNavigate={handleNavigate}>
      <Suspense fallback={<PageLoader />}>
        {activePage === 'chat' ? <ChatPage /> : <KnowledgeBasePage />}
      </Suspense>
    </AppShell>
  );
}

export default App;

