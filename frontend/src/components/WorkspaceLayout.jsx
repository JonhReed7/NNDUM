import { useEffect, useRef, useState } from 'react';
import { Menu, X } from 'lucide-react';
import { Brand } from './PromoPanel.jsx';
import { DesignIcon, Modal, WorkspaceButton } from './WorkspaceUI.jsx';
import { artwork, figmaAsset } from '../assets/figma.js';

const reportLinks = [
  { route: 'analysis', label: 'Новый анализ', symbol: '＋' },
  { route: 'dashboard', label: 'Дашборд', symbol: '▥' },
  { route: 'report', label: 'Отчёт', symbol: '▤' },
  { route: 'methodology', label: 'Методика', symbol: '◇' },
];

export function WorkspaceLayout({ route, teams, userName, onNameChange, children }) {
  const compact = route === 'report';
  const [reportsOpen, setReportsOpen] = useState(true);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [popover, setPopover] = useState(null);
  const [modal, setModal] = useState(null);
  const header = useRef(null);

  useEffect(() => {
    setMobileOpen(false);
    setPopover(null);
  }, [route]);
  useEffect(() => {
    function dismiss(event) {
      if (event.type === 'keydown' && event.key === 'Escape') {
        setPopover(null);
        setMobileOpen(false);
      }
      if (event.type === 'pointerdown' && !header.current?.contains(event.target)) setPopover(null);
    }
    document.addEventListener('pointerdown', dismiss);
    document.addEventListener('keydown', dismiss);
    return () => {
      document.removeEventListener('pointerdown', dismiss);
      document.removeEventListener('keydown', dismiss);
    };
  }, []);

  function reportLink(item) {
    const active = route === item.route;
    return (
      <a
        key={item.route}
        href={`#/${item.route}`}
        aria-current={active ? 'page' : undefined}
        className={`report-link ${active ? 'is-active' : ''}`}
      >
        <span className="report-symbol" aria-hidden="true">
          {!compact && route !== 'home' && item.route !== 'analysis'
            ? `  ${item.symbol}`
            : item.symbol}
        </span>
        <span>{item.label}</span>
      </a>
    );
  }

  return (
    <div className={`workspace ${compact ? 'workspace--report' : ''} workspace--${route}`}>
      <header className="workspace-header" ref={header}>
        <button
          type="button"
          className="icon-button mobile-menu-toggle"
          aria-label={mobileOpen ? 'Закрыть меню' : 'Открыть меню'}
          aria-expanded={mobileOpen}
          aria-controls="workspace-sidebar"
          onClick={() => setMobileOpen(!mobileOpen)}
        >
          {mobileOpen ? <X size={22} /> : <Menu size={22} />}
        </button>
        {compact ? (
          <a href="#/home" className="report-brand" aria-label="DevPulse — главная">
            <span
              className="report-brand-mark"
              aria-hidden="true"
              style={artwork('report-vector4')}
            >
              <img src={figmaAsset('report-vector5')} alt="" />
              <img src={figmaAsset('report-vector6')} alt="" />
              <img src={figmaAsset('report-vector7')} alt="" />
            </span>
            DevPulse
          </a>
        ) : (
          <Brand href="#/home" label="DevPulse — главная" />
        )}
        {compact ? (
          <span className="demo-label">● Демо-данные</span>
        ) : (
          <div className="header-actions">
            <div className="header-popover-anchor">
              <button
                type="button"
                className="team-switcher"
                aria-expanded={popover === 'teams'}
                onClick={() => setPopover(popover === 'teams' ? null : 'teams')}
              >
                <span className="team-dot" />
                Мои команды
                <DesignIcon name="home-svg16" />
              </button>
              {popover === 'teams' && (
                <div className="header-popover">
                  <p>Мои команды</p>
                  {teams.map((team) => (
                    <a
                      key={team.id}
                      href={`#/home?section=teams&team=${team.id}`}
                      onClick={() => setPopover(null)}
                    >
                      {team.name}
                    </a>
                  ))}
                </div>
              )}
            </div>
            <div className="header-popover-anchor">
              <button
                type="button"
                className="icon-button notification-button"
                aria-label="Уведомления"
                aria-expanded={popover === 'notifications'}
                onClick={() => setPopover(popover === 'notifications' ? null : 'notifications')}
              >
                <DesignIcon name="home-svg17" />
              </button>
              {popover === 'notifications' && (
                <div className="header-popover">
                  <strong>Уведомления</strong>
                  <p>Новых уведомлений пока нет.</p>
                </div>
              )}
            </div>
            <div className="header-popover-anchor">
              <button
                type="button"
                className="profile-button"
                aria-label="Меню профиля"
                aria-expanded={popover === 'profile'}
                onClick={() => setPopover(popover === 'profile' ? null : 'profile')}
              >
                АИ
              </button>
              {popover === 'profile' && (
                <div className="header-popover">
                  <strong>{userName}</strong>
                  <button
                    type="button"
                    onClick={() => {
                      setModal('settings');
                      setPopover(null);
                    }}
                  >
                    Настройки профиля
                  </button>
                  <a href="#/login">Выйти</a>
                </div>
              )}
            </div>
          </div>
        )}
      </header>
      {mobileOpen && (
        <button
          type="button"
          className="sidebar-overlay"
          aria-label="Закрыть меню"
          onClick={() => setMobileOpen(false)}
        />
      )}
      <aside id="workspace-sidebar" className={`workspace-sidebar ${mobileOpen ? 'is-open' : ''}`}>
        <nav aria-label="Основная навигация">
          {compact ? (
            <>
              <p className="nav-caption">РАБОЧАЯ ОБЛАСТЬ</p>
              <div className="compact-report-links">{reportLinks.map(reportLink)}</div>
            </>
          ) : (
            <>
              <a
                href="#/home"
                className={`workspace-nav-link workspace-nav-link--home ${route === 'home' ? 'is-active' : ''}`}
                aria-current={route === 'home' ? 'page' : undefined}
              >
                <DesignIcon name="home-svg10" />
                Главная
              </a>
              <a href="#/home?section=projects" className="workspace-nav-link">
                <DesignIcon name="home-svg11" />
                Проекты
              </a>
              <a href="#/home?section=teams" className="workspace-nav-link">
                <DesignIcon name="home-svg12" />
                Команды
              </a>
              <button
                type="button"
                className="workspace-nav-link reports-toggle"
                aria-expanded={reportsOpen}
                aria-controls="report-navigation"
                onClick={() => setReportsOpen(!reportsOpen)}
              >
                <DesignIcon name="home-svg13" />
                Отчёты
                <DesignIcon
                  name="home-svg14"
                  className={`reports-chevron ${reportsOpen ? 'is-open' : ''}`}
                />
              </button>
              {reportsOpen && (
                <div id="report-navigation" className="report-submenu">
                  {reportLinks.filter((item) => item.route !== 'report').map(reportLink)}
                </div>
              )}
              <button
                type="button"
                className="workspace-nav-link"
                onClick={() => setModal('settings')}
              >
                <DesignIcon name="home-svg15" />
                Настройки
              </button>
            </>
          )}
        </nav>
        {!compact && (
          <div className="workspace-help">
            <strong>Нужна помощь?</strong>
            <p>
              Посмотрите руководство
              <br />
              по работе с сервисом
            </p>
            <button type="button" className="text-link" onClick={() => setModal('help')}>
              Открыть гайд
            </button>
          </div>
        )}
      </aside>
      <main id="workspace-main" className="workspace-main" aria-labelledby="page-title" key={route}>
        {children}
      </main>
      {modal === 'help' && (
        <Modal title="Руководство DevPulse" onClose={() => setModal(null)}>
          <ol className="guide-steps">
            <li>Откройте «Новый анализ» и выберите команду.</li>
            <li>Укажите URL репозитория, ветку и период.</li>
            <li>Запустите демонстрационный анализ и изучите дашборд.</li>
            <li>Откройте отчёт для выгрузки CSV или методику, чтобы узнать правила расчёта.</li>
          </ol>
          <p className="dialog-note">
            Сейчас сервис показывает демо-данные. Подключение репозитория и расчёт на сервере ещё не
            реализованы.
          </p>
          <WorkspaceButton href="#/analysis" onClick={() => setModal(null)}>
            Перейти к анализу
          </WorkspaceButton>
        </Modal>
      )}
      {modal === 'settings' && (
        <Modal title="Настройки профиля" onClose={() => setModal(null)}>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              onNameChange(new FormData(event.currentTarget).get('displayName').trim());
              setModal(null);
            }}
          >
            <label className="workspace-field">
              Имя
              <input
                name="displayName"
                defaultValue={userName}
                required
                maxLength={50}
                pattern=".*\S.*"
              />
            </label>
            <p className="dialog-note">Имя используется в приветствии в этой демо-сессии.</p>
            <WorkspaceButton type="submit">Сохранить</WorkspaceButton>
          </form>
        </Modal>
      )}
    </div>
  );
}
