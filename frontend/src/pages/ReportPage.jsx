import { PageHeading, Surface, WorkspaceButton } from '../components/WorkspaceUI.jsx';
import { artwork } from '../assets/figma.js';
import { formatPeriod, metrics } from '../data/demo.js';
import { downloadReportCsv } from '../services/report.js';

export function ReportPage({ analysis, teamName, printable = false }) {
  const passport = [
    ['Источник', 'Т1 Код · демо'],
    ['Ветка', analysis.branch],
    ['Хэш снимка', analysis.commit || 'Не указан'],
    ['Часовой пояс', 'UTC+5'],
    ['Покрытие', '8 из 8 метрик'],
  ];
  return (
    <>
      <PageHeading
        headingId={printable ? 'print-report-title' : 'page-title'}
        title="Отчёт за спринт"
        description={`${teamName} · ${formatPeriod(analysis)}`}
        projectName={analysis.projectName}
        action={
          !printable && (
            <WorkspaceButton
              art="report-vector9"
              onClick={() => downloadReportCsv(analysis, teamName)}
            >
              Скачать CSV
            </WorkspaceButton>
          )
        }
      />
      <div className="report-grid">
        <Surface art="report-vector10" className="sprint-results">
          <h2>Итоги спринта</h2>
          <div className="table-scroll">
            <table className="results-table">
              <thead>
                <tr>
                  <th scope="col">Метрика</th>
                  <th scope="col">Значение</th>
                </tr>
              </thead>
              <tbody>
                {metrics.map((metric) => (
                  <tr key={metric.name} style={artwork('report-vector12')}>
                    <th scope="row">{metric.name}</th>
                    <td>{metric.value}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Surface>
        <Surface art="report-vector11" className="report-passport">
          <h2>Паспорт отчёта</h2>
          <p className="section-description">Параметры для повторного расчёта</p>
          <dl>
            {passport.map(([label, value]) => (
              <div key={label} style={artwork('report-vector13')}>
                <dt>{label}</dt>
                <dd>{value}</dd>
              </div>
            ))}
          </dl>
          <div className="sprint-signal" style={artwork('report-vector14')}>
            <strong>Сигнал спринта</strong>
            <p>Первый отклик на PR стал быстрее.</p>
            <p>Две ветки требуют уточнения статуса.</p>
          </div>
          <a href="#/methodology" className="methodology-link">
            Открыть методику расчёта
          </a>
        </Surface>
      </div>
      {printable && (
        <p className="print-demo-note">
          DevPulse · Демонстрационные данные · {analysis.repository}
        </p>
      )}
    </>
  );
}
