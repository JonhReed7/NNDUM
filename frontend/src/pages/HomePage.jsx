import { useEffect, useRef, useState } from 'react';
import { DesignIcon, Modal, Surface, WorkspaceButton } from '../components/WorkspaceUI.jsx';
import { projects } from '../data/demo.js';

export function HomePage({ teams, onCreateTeam, onConnect, onOpenProject, userName, search = '' }) {
  const params = new URLSearchParams(search);
  const teamFilter = params.get('team') || '';
  const section = params.get('section');
  const [query, setQuery] = useState('');
  const [teamOffset, setTeamOffset] = useState(0);
  const [creating, setCreating] = useState(false);
  const [teamError, setTeamError] = useState('');
  const teamsSection = useRef(null);
  const projectsSection = useRef(null);
  const visibleTeams = [...teams.slice(teamOffset), ...teams.slice(0, teamOffset)].slice(0, 3);
  const visibleProjects = projects.filter(
    (project) =>
      (!teamFilter || project.teamId === teamFilter) &&
      `${project.name} ${project.repository}`.toLowerCase().includes(query.toLowerCase()),
  );

  useEffect(() => {
    if (section)
      (section === 'teams' ? teamsSection : projectsSection).current?.scrollIntoView({
        block: 'start',
      });
  }, [section, teamFilter]);

  function createTeam(event) {
    event.preventDefault();
    const name = new FormData(event.currentTarget).get('teamName').trim();
    if (!name || teams.some((team) => team.name.toLowerCase() === name.toLowerCase())) {
      setTeamError('Укажите уникальное название команды.');
      return;
    }
    onCreateTeam(name);
    setTeamOffset(teams.length);
    setCreating(false);
  }

  return (
    <>
      <header className="home-heading">
        <div>
          <p className="eyebrow">ОБЗОР</p>
          <h1 id="page-title">Добро пожаловать, {userName}!</h1>
          <p>Вот что происходит в ваших командах сегодня.</p>
        </div>
        <time dateTime="2025-05-14">14 мая 2025</time>
      </header>
      <Surface className="connect-panel">
        <h2>Подключить репозиторий</h2>
        <p className="section-description">
          Вставьте ссылку, выберите команду — остальное сделаем мы.
        </p>
        <form
          className="connect-form"
          onSubmit={(event) => {
            event.preventDefault();
            const data = new FormData(event.currentTarget);
            onConnect(data.get('repository'), data.get('teamId'));
          }}
        >
          <label className="connect-input">
            <span className="sr-only">URL репозитория</span>
            <DesignIcon name="home-svg" />
            <input
              name="repository"
              type="url"
              pattern="https?://.+"
              placeholder="https://github.com/user/repo"
              required
            />
          </label>
          <label className="connect-team">
            <span className="sr-only">Выберите команду</span>
            <select name="teamId" defaultValue={teamFilter} required>
              <option value="" disabled>
                Выберите команду
              </option>
              {teams.map((team) => (
                <option key={team.id} value={team.id}>
                  {team.name}
                </option>
              ))}
            </select>
          </label>
          <WorkspaceButton type="submit">Загрузить</WorkspaceButton>
        </form>
      </Surface>
      <section ref={teamsSection} className="home-section" aria-labelledby="teams-title">
        <div className="section-heading">
          <div>
            <h2 id="teams-title">Мои команды</h2>
            <p className="section-description">Команды, в которых вы состоите</p>
          </div>
          <WorkspaceButton
            secondary
            onClick={() => {
              setTeamError('');
              setCreating(true);
            }}
          >
            <DesignIcon name="home-svg1" />
            Создать команду
          </WorkspaceButton>
        </div>
        <div className="team-carousel">
          <button
            type="button"
            className="circle-button carousel-previous"
            aria-label="Предыдущие команды"
            onClick={() => setTeamOffset((teamOffset + teams.length - 1) % teams.length)}
          >
            <DesignIcon name="home-svg2" />
          </button>
          <div className="team-cards">
            {visibleTeams.map((team) => (
              <Surface as="article" className={`team-card team-card--${team.tone}`} key={team.id}>
                <div className="team-card-top">
                  <span className="team-card-icon">
                    <DesignIcon
                      name={
                        team.tone === 'cyan'
                          ? 'home-svg5'
                          : team.tone === 'violet'
                            ? 'home-svg6'
                            : 'home-svg3'
                      }
                    />
                  </span>
                  <span className="team-role">{team.role}</span>
                </div>
                <h3>{team.name}</h3>
                <p>{team.projects}</p>
                <div className="team-card-bottom">
                  <div
                    className="member-avatars"
                    aria-label={`Участники: ${team.members.join(', ')}`}
                  >
                    {team.members.map((member) => (
                      <span key={member}>{member}</span>
                    ))}
                  </div>
                  <a
                    className="circle-button"
                    href={`#/home?section=projects&team=${team.id}`}
                    aria-label={`Проекты команды ${team.name}`}
                  >
                    <DesignIcon name="home-svg4" />
                  </a>
                </div>
              </Surface>
            ))}
          </div>
          <button
            type="button"
            className="circle-button"
            aria-label="Следующие команды"
            onClick={() => setTeamOffset((teamOffset + 1) % teams.length)}
          >
            <DesignIcon name="home-svg2" />
          </button>
        </div>
      </section>
      <section
        ref={projectsSection}
        className="home-section projects-section"
        aria-labelledby="projects-title"
      >
        <div className="section-heading">
          <div>
            <h2 id="projects-title">Мои проекты</h2>
            <p className="section-description">Последние добавленные проекты</p>
          </div>
          <a className="all-projects" href="#/home?section=projects" onClick={() => setQuery('')}>
            Все проекты
            <DesignIcon name="home-svg7" />
          </a>
        </div>
        <div className="project-search-row">
          <label className="project-search">
            <DesignIcon name="home-svg8" />
            <span className="sr-only">Найти проект</span>
            <input
              type="search"
              placeholder="Найти проект"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
          </label>
          {teamFilter && (
            <a className="clear-filter" href="#/home?section=projects">
              {teams.find((team) => team.id === teamFilter)?.name} · Сбросить
            </a>
          )}
        </div>
        <div className="table-scroll project-table-wrapper">
          <table className="project-table">
            <thead>
              <tr>
                <th scope="col">Проект</th>
                <th scope="col">Команда</th>
                <th scope="col">Последний анализ</th>
                <th scope="col">Статус</th>
                <th scope="col">
                  <span className="sr-only">Действие</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {visibleProjects.map((project) => (
                <tr key={project.id}>
                  <td>
                    <div className="project-name">
                      <span className="project-icon">
                        <DesignIcon name="home-svg9" />
                      </span>
                      <div>
                        <strong>{project.name}</strong>
                        <small>{project.repository}</small>
                      </div>
                    </div>
                  </td>
                  <td>{teams.find((team) => team.id === project.teamId)?.name}</td>
                  <td>{project.lastAnalysis}</td>
                  <td>
                    <span className={`status-badge status-badge--${project.status}`}>
                      {project.status === 'ready' ? '✓ Готов' : '↻ Анализируется'}
                    </span>
                  </td>
                  <td>
                    <button
                      type="button"
                      className="text-link"
                      onClick={() => onOpenProject(project)}
                    >
                      Открыть
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {visibleProjects.length === 0 && (
            <p className="empty-state">
              Проекты не найдены. Измените поиск или выберите другую команду.
            </p>
          )}
        </div>
      </section>
      {creating && (
        <Modal title="Создать команду" onClose={() => setCreating(false)}>
          <form onSubmit={createTeam}>
            <label className="workspace-field">
              Название команды
              <input
                name="teamName"
                placeholder="Например, Команда Альфа"
                required
                maxLength={60}
                onChange={() => setTeamError('')}
                aria-invalid={Boolean(teamError)}
                aria-describedby={teamError ? 'team-error' : undefined}
              />
            </label>
            {teamError && (
              <p id="team-error" className="workspace-error" role="alert">
                {teamError}
              </p>
            )}
            <p className="dialog-note">Команда будет доступна в течение этой демо-сессии.</p>
            <WorkspaceButton type="submit">Создать команду</WorkspaceButton>
          </form>
        </Modal>
      )}
    </>
  );
}
