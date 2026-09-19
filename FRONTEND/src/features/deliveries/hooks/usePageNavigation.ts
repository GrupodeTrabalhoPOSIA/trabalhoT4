import { useEffect, useState } from 'react';
import { pageFromHash, pageTitles } from '../utils/catalogue';

function initialLocation() {
  const page = pageFromHash(window.location.hash);
  return { page, visitedT4: page === 't4', visitedT5: page === 't5', visitedT6: page === 't6' };
}

/** Hash URLs allow direct links on static hosting, without server routing. */
export function usePageNavigation() {
  const [location, setLocation] = useState(initialLocation);
  useEffect(() => {
    function navigate() {
      const page = pageFromHash(window.location.hash);
      setLocation(previous => ({ page, visitedT4: previous.visitedT4 || page === 't4', visitedT5: previous.visitedT5 || page === 't5', visitedT6: previous.visitedT6 || page === 't6' }));
    }
    window.addEventListener('hashchange', navigate);
    return () => window.removeEventListener('hashchange', navigate);
  }, []);
  useEffect(() => {
    document.title = `Aurora Tech · ${pageTitles[location.page]}`;
    document.getElementById('main-content')?.focus({ preventScroll: true });
    window.scrollTo({ top: 0, behavior: 'instant' });
  }, [location.page]);
  return location;
}
