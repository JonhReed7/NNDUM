import { PageHeading, Surface, WorkspaceButton } from '../components/WorkspaceUI.jsx';
import { figmaAsset, artwork } from '../assets/figma.js';
import { contributors, formatPeriod, metrics } from '../data/demo.js';

export function DashboardPage({ analysis, teamName, onPrint }) {
  return (
    <>
      <PageHeading
        title="Дашборд команды"
        description={`${analysis.projectName} · ${teamName}`}
        projectName={analysis.projectName}
        action={
          <WorkspaceButton href="#/methodology" art="dashboard-vector9">
            Открыть Методику
          </WorkspaceButton>
        }
      >
        <div className="sprint-toolbar">
          <span className="sprint-period" style={artwork('dashboard-vector10')}>
            Спринт 4 · {formatPeriod(analysis, true)}
          </span>
          <span className="branch-label">⌘ {analysis.branch}</span>
        </div>
      </PageHeading>
      <div className="metric-cards">
        {metrics.slice(0, 4).map((metric) => (
          <Surface as="article" key={metric.name} art="dashboard-vector11" className="metric-card">
            <h2>{metric.name}</h2>
            <strong>{metric.value}</strong>
            <p>{metric.note}</p>
          </Surface>
        ))}
      </div>
      <div className="dashboard-grid">
        <Surface art="dashboard-vector12" className="activity-panel">
          <h2>Динамика работы</h2>
          <p className="section-description">Коммиты по неделям спринта</p>
          <div
            className="activity-chart"
            role="img"
            aria-label="Коммиты по неделям спринта: неделя 1 — 21, неделя 2 — 29, неделя 3 — 38."
          >
            <div className="activity-gridlines" aria-hidden="true">
              {[0, 1, 2, 3].map((line) => (
                <span key={line} style={artwork('dashboard-vector14')} />
              ))}
            </div>
            <div className="activity-bars" aria-hidden="true">
              {[21, 29, 38].map((value, index) => (
                <div className="activity-column" key={value}>
                  <div className="activity-bar">
                    <strong>{value}</strong>
                    <img src={figmaAsset(`dashboard-vector${15 + index}`)} alt="" />
                  </div>
                  <span>Нед. {index + 1}</span>
                </div>
              ))}
            </div>
          </div>
        </Surface>
        <Surface art="dashboard-vector13" className="discussion-panel">
          <h2>Что обсудить</h2>
          <p className="section-description">Сигналы для ретроспективы</p>
          <div className="signal signal--warning" style={artwork('dashboard-vector18')}>
            <strong>2 ветки без активности</strong>
            <p>Уточните статус задач на синке.</p>
          </div>
          <div className="signal" style={artwork('dashboard-vector19')}>
            <strong>Ревью стало быстрее</strong>
            <p>Медиана первого ответа снизилась с 14 до 9 ч.</p>
          </div>
        </Surface>
        <Surface art="dashboard-vector20" className="contributors-panel">
          <h2>Вклад команды</h2>
          <div className="table-scroll">
            <table className="contributors-table">
              <thead>
                <tr>
                  <th scope="col">Участник</th>
                  <th scope="col">Коммиты</th>
                  <th scope="col">PR</th>
                  <th scope="col">Ревью</th>
                </tr>
              </thead>
              <tbody>
                {contributors.map((person) => (
                  <tr key={person.name} style={artwork('dashboard-vector14')}>
                    <th scope="row">{person.name}</th>
                    <td>{person.commits}</td>
                    <td>{person.prs}</td>
                    <td>{person.reviews}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Surface>
        <Surface art="dashboard-vector21" className="dashboard-report-panel">
          <h2>
            <a href="#/report">Отчет</a>
          </h2>
          <a className="section-description report-description" href="#/report">
            Полный отчет по метрикам
          </a>
          <dl className="dashboard-report-stats">
            <div style={artwork('dashboard-vector23')}>
              <dt>Покрытие</dt>
              <dd>9 из 9 метрик</dd>
            </div>
            <div style={artwork('dashboard-vector23')}>
              <dt>Чистота репозитория</dt>
              <dd>0 файлов</dd>
            </div>
          </dl>
          <WorkspaceButton art="dashboard-vector22" onClick={onPrint}>
            Скачать PDF
          </WorkspaceButton>
        </Surface>
      </div>
    </>
  );
}
