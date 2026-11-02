import { useEffect, useState } from 'react';
import { LoginPage } from './pages/LoginPage.jsx';
import { RegisterPage } from './pages/RegisterPage.jsx';

function getRoute() {
  if (window.location.hash.startsWith('#/')) {
    return window.location.hash.startsWith('#/register') ? 'register' : 'login';
  }
  return window.location.pathname.replace(/\/$/, '') === '/register' ? 'register' : 'login';
}

export function App() {
  const [route, setRoute] = useState(getRoute);
  useEffect(() => {
    function updateRoute() { setRoute(getRoute()); }
    window.addEventListener('hashchange', updateRoute);
    return () => window.removeEventListener('hashchange', updateRoute);
  }, []);
  useEffect(() => {
    document.title = `${route === 'register' ? 'Регистрация' : 'Вход'} — DevPulse`;
  }, [route]);

  // The demo preserves the registration error state visible in the Figma reference.
  return route === 'register' ? <RegisterPage previewError /> : <LoginPage />;
}
