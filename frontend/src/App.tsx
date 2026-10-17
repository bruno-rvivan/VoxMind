import { Navigate, NavLink, Outlet, Route, Routes, useLocation, useNavigate } from 'react-router-dom';

import AnalysisPage from './pages/AnalysisPage';
import DashboardPage from './pages/DashboardPage';
import HistoryPage from './pages/HistoryPage';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import UploadPage from './pages/UploadPage';
import { clearToken } from './services/api';

function ProtectedRoute() {
  const token = localStorage.getItem('voxmind_token');
  const location = useLocation();

  if (!token) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return <Outlet />;
}

function AppShell() {
  const navigate = useNavigate();
  const token = localStorage.getItem('voxmind_token');

  const handleLogout = () => {
    clearToken();
    navigate('/login');
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-wrap">
          <div className="brand-mark">V</div>
          <div>
            <strong>VoxMind</strong>
            <small>Inteligência de apresentação</small>
          </div>
        </div>

        <nav className="main-nav" aria-label="Menu principal">
          <NavLink to="/">Início</NavLink>
          {!token ? (
            <NavLink to="/login">Entrar</NavLink>
          ) : (
            <>
              <NavLink to="/dashboard">Dashboard</NavLink>
              <NavLink to="/upload">Upload</NavLink>
              <NavLink to="/analysis">Relatório</NavLink>
              <NavLink to="/history">Histórico</NavLink>
              <button type="button" className="nav-logout" onClick={handleLogout}>
                Sair
              </button>
            </>
          )}
        </nav>
      </header>

      <main className="page-panel">
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route element={<ProtectedRoute />}>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/analysis" element={<AnalysisPage />} />
            <Route path="/history" element={<HistoryPage />} />
          </Route>
        </Routes>
      </main>
    </div>
  );
}

export default function App() {
  return <AppShell />;
}
