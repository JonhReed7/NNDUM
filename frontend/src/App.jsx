import { useEffect, useState } from 'react';
import { LoginPage } from './pages/LoginPage.jsx';
import { RegisterPage } from './pages/RegisterPage.jsx';
import { WorkspaceLayout } from './components/WorkspaceLayout.jsx';
import { HomePage } from './pages/HomePage.jsx';
import { AnalysisPage } from './pages/AnalysisPage.jsx';
import { DashboardPage } from './pages/DashboardPage.jsx';
import { ReportPage } from './pages/ReportPage.jsx';
import { MethodologyPage } from './pages/MethodologyPage.jsx';
import { defaultAnalysis, initialTeams } from './data/demo.js';

const titles = {
  login: 'Вход',
  register: 'Регистрация',
  home: 'Главная',
  analysis: 'Новый анализ',
  dashboard: 'Дашборд команды',
  report: 'Отчёт за спринт',
  methodology: 'Методика расчёта',
};

function getRoute() {
  const location = window.location.hash.startsWith('#/')
    ? window.location.hash.slice(1)
    : window.location.pathname;
  const [path, search = ''] = location.split('?');
  const route = path.replace(/^\/|\/$/g, '') || 'login';
  return { name: Object.hasOwn(titles, route) ? route : 'login', search };
}

export function App() {
  const [route, setRoute] = useState(getRoute);
  const [teams, setTeams] = useState(initialTeams);
  const [analysis, setAnalysis] = useState(defaultAnalysis);
  const [userName, setUserName] = useState('Максим');
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
    if (!new URLSearchParams(route.search).has('section')) window.scrollTo(0, 0);
  }, [route.name, route.search]);

  function navigate(name) {
    window.location.hash = `#/${name}`;
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

  // Preserve the existing registration preview and keep demo access explicit.
  if (route.name === 'register') return <RegisterPage previewError />;
  if (route.name === 'login') return <LoginPage onDemo={() => navigate('home')} />;

  return (
    <>
      <WorkspaceLayout
        route={route.name}
        teams={teams}
        userName={userName}
        onNameChange={setUserName}
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
