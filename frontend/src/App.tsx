import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAuthStore } from './store/authStore';
import Sidebar from './components/layout/Sidebar';
import Topbar from './components/layout/Topbar';
import Login from './pages/Login';
import Overview from './pages/Overview';
import Shelves from './pages/Shelves';
import Compliance from './pages/Compliance';
import Forecast from './pages/Forecast';
import Alerts from './pages/Alerts';
import Analytics from './pages/Analytics';
import Festival from './pages/Festival';
import Settings from './pages/Settings';
import './i18n';

const queryClient = new QueryClient({
  defaultOptions: { queries: { refetchOnWindowFocus: false, retry: 1 } },
});

const pageTitles: Record<string, string> = {
  '/': 'Overview',
  '/shelves': 'Shelf Monitoring',
  '/compliance': 'Planogram Compliance',
  '/forecast': 'Demand Forecast',
  '/alerts': 'Alert Center',
  '/analytics': 'Analytics',
  '/festival': 'Festival Dashboard',
  '/settings': 'Settings',
};

function ProtectedLayout() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  const title = pageTitles[location.pathname] || 'ShelfIQ';

  return (
    <div className="app-shell">
      <Sidebar />
      <main className="main-content">
        <Topbar title={title} />
        <div className="page-content">
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/shelves" element={<Shelves />} />
            <Route path="/compliance" element={<Compliance />} />
            <Route path="/forecast" element={<Forecast />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/festival" element={<Festival />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/*" element={<ProtectedLayout />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
