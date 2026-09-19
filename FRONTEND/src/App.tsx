import { lazy, Suspense } from 'react';

import AppShell from '@/components/AppShell';
import PageLoader from '@/components/PageLoader';
import { usePageNavigation } from '@/features/deliveries/hooks/usePageNavigation';

const ChatPage = lazy(() => import('@/pages/ChatPage'));
const KnowledgeBasePage = lazy(() => import('@/pages/KnowledgeBasePage'));
const T4Page = lazy(() => import('@/features/t4/screens/T4Page'));
const OverviewPage = lazy(() => import('@/features/deliveries/screens/OverviewPage'));
const ReportPage = lazy(() => import('@/features/deliveries/screens/ReportPage'));
const AboutPage = lazy(() => import('@/features/deliveries/screens/AboutPage'));

function App() {
  const { page: activePage, visitedT4 } = usePageNavigation();

  return (
    <AppShell activePage={activePage}>
      <Suspense fallback={<PageLoader />}>
        {visitedT4 && <div hidden={activePage !== 't4'}><T4Page /></div>}
        {activePage === 'overview' && <OverviewPage />}
        {activePage === 'about' && <AboutPage />}
        {(activePage === 't1' || activePage === 't2' || activePage === 't3') && <ReportPage id={activePage} />}
        {activePage === 'chat' ? <ChatPage /> : activePage === 'knowledge' ? <KnowledgeBasePage /> : null}
      </Suspense>
    </AppShell>
  );
}

export default App;

