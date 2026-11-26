import { useCallback, useEffect, useRef, useState } from 'react';
import { LoginPage } from './pages/LoginPage.jsx';
import { RegisterPage } from './pages/RegisterPage.jsx';
import { WorkspaceLayout } from './components/WorkspaceLayout.jsx';
import { HomePage } from './pages/HomePage.jsx';
import { AnalysisPage } from './pages/AnalysisPage.jsx';
import { DashboardPage } from './pages/DashboardPage.jsx';
import { ReportPage } from './pages/ReportPage.jsx';
import { MethodologyPage } from './pages/MethodologyPage.jsx';
import { defaultAnalysis, initialTeams } from './data/demo.js';
import { clearAuthSession, getAuthSession, login, register, saveAuthSession } from './services/api.js';
import { completeOAuth } from './services/oauth.js';

const titles = {
  login: 'Вход',
  register: 'Регистрация',
  home: 'Главная',
  analysis: 'Новый анализ',
  dashboard: 'Дашборд команды',
  report: 'Отчёт за спринт',
  methodology: 'Методика расчёта',
};

const demoUserName = 'Максим';

function getUserName(user) {
  return user?.first_name || user?.username || user?.email || demoUserName;
}

function getRoute() {
  const location = window.location.hash.startsWith('#/')
    ? window.location.hash.slice(1)
    : window.location.pathname;
  const [path, search = ''] = location.split('?');
  const route = path.replace(/^\/|\/$/g, '') || (getAuthSession() ? 'home' : 'login');
  return { name: Object.hasOwn(titles, route) ? route : 'login', search };
}

function navigate(name) {
  window.location.hash = `#/${name}`;
}

export function App({ oauthCallback }) {
  const [route, setRoute] = useState(getRoute);
  const [teams, setTeams] = useState(initialTeams);
  const [analysis, setAnalysis] = useState(defaultAnalysis);
  const [userName, setUserName] = useState(() => getUserName(getAuthSession()?.user));
  const [callbackError, setCallbackError] = useState(oauthCallback?.error);
  const [callbackPending, setCallbackPending] = useState(Boolean(oauthCallback?.code));
  const oauthExchange = useRef(null);

  const finishAuth = useCallback((session, remember) => {
    saveAuthSession(session, remember);
    setUserName(getUserName(session.user));
    navigate('home');
  }, []);

  useEffect(() => {
    function updateRoute() {
      setRoute(getRoute());
    }
    window.addEventListener('hashchange', updateRoute);
    window.addEventListener('popstate', updateRoute);
    return () => {
      window.removeEventListener('hashchange', updateRoute);
      window.removeEventListener('popstate', updateRoute);
    };
  }, []);
  useEffect(() => {
    document.title = `${titles[route.name]} — DevPulse`;
    if (route.name === 'login' || route.name === 'register') window.scrollTo(0, 0);
  }, [route.name, route.search]);

  useEffect(() => {
    if (!oauthCallback?.code) return;

    // The provider code is single-use, including during StrictMode's second effect setup.
    oauthExchange.current ??= completeOAuth(oauthCallback.provider, oauthCallback.code);
    let active = true;
    async function finishCallback() {
      try {
        const session = await oauthExchange.current;
        if (active) finishAuth(session, oauthCallback.remember);
      } catch (error) {
        if (active) setCallbackError(error.message);
      } finally {
        if (active) setCallbackPending(false);
      }
    }

    finishCallback();
    return () => { active = false; };
  }, [oauthCallback, finishAuth]);

  async function handleLogin(formData, signal) {
    const session = await login({
      email: formData.get('email'),
      password: formData.get('password'),
    }, signal);
    if (!signal.aborted) finishAuth(session, formData.has('remember'));
  }

  async function handleRegister(formData, signal) {
    const session = await register({
      email: formData.get('email'),
      password: formData.get('password'),
      username: formData.get('username'),
      first_name: formData.get('firstName'),
      last_name: formData.get('lastName'),
    }, signal);
    if (!signal.aborted) finishAuth(session);
  }

  function handleLogout() {
    clearAuthSession();
    setUserName(demoUserName);
    navigate('login');
  }

  function connect(repository, teamId) {
    const projectName =
      repository
        .replace(/\/$/, '')
        .split('/')
        .pop()
        .replace(/\.git$/, '') || 'Новый проект';
    setAnalysis({ ...defaultAnalysis, repository, teamId, projectName, commit: '' });
    navigate('analysis');
  }

  function openProject(project) {
    setAnalysis({
      ...defaultAnalysis,
      projectName: project.name,
      repository: `https://github.com/${project.repository}`,
      teamId: project.teamId,
    });
    navigate(project.status === 'processing' ? 'analysis' : 'dashboard');
  }

  const selectedTeam = teams.find((team) => team.id === analysis.teamId);
  const teamName = selectedTeam?.reportName || selectedTeam?.name || 'Команда «Альфа»';

  const authPageProps = {
    callbackPending,
    callbackError: oauthCallback?.mode === route.name ? callbackError : undefined,
  };
  if (route.name === 'register') return <RegisterPage onSubmit={handleRegister} {...authPageProps} />;
  if (route.name === 'login') {
    return <LoginPage onSubmit={handleLogin} onDemo={() => navigate('home')} {...authPageProps} />;
  }

  return (
    <>
      <WorkspaceLayout
        route={route.name}
        search={route.search}
        teams={teams}
        userName={userName}
        onNameChange={setUserName}
        onLogout={handleLogout}
      >
        {route.name === 'home' && (
          <HomePage
            teams={teams}
            userName={userName}
            search={route.search}
            onConnect={connect}
            onOpenProject={openProject}
            onCreateTeam={(name) =>
              setTeams([
                ...teams,
                {
                  id: `team-${Date.now()}`,
                  name,
                  role: 'Владелец',
                  projects: '0 проектов',
                  members: ['АИ'],
                  tone: 'blue',
                },
              ])
            }
          />
        )}
        {route.name === 'analysis' && (
          <AnalysisPage
            key={`${analysis.repository}-${analysis.teamId}`}
            analysis={analysis}
            teams={teams}
            onStart={(data) => {
              setAnalysis(data);
              navigate('dashboard');
            }}
          />
        )}
        {route.name === 'dashboard' && (
          <DashboardPage analysis={analysis} teamName={teamName} onPrint={() => window.print()} />
        )}
        {route.name === 'report' && <ReportPage analysis={analysis} teamName={teamName} />}
        {route.name === 'methodology' && <MethodologyPage analysis={analysis} />}
      </WorkspaceLayout>
      <div className="print-report">
        <ReportPage analysis={analysis} teamName={teamName} printable />
      </div>
    </>
  );
}
