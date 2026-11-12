import { PageHeading, Surface } from '../components/WorkspaceUI.jsx';
import { artwork } from '../assets/figma.js';
import { metrics } from '../data/demo.js';

export function MethodologyPage({ analysis }) {
  return (
    <>
      <PageHeading
        title="Методика расчёта"
        description="Источники, правила расчёта и ограничения показателей"
        projectName={analysis.projectName}
      />
      <Surface art="methodology-vector9" className="methodology-panel">
        <h2>Восемь метрик MVP</h2>
        <div className="table-scroll">
          <table className="methodology-table">
            <thead>
              <tr>
                <th scope="col">Метрика</th>
                <th scope="col">Как считаем</th>
                <th scope="col">Источник</th>
              </tr>
            </thead>
            <tbody>
              {metrics.map((metric) => (
                <tr key={metric.name} style={artwork('methodology-vector10')}>
                  <th scope="row">{metric.name}</th>
                  <td>{metric.formula}</td>
                  <td>{metric.source}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="methodology-note" style={artwork('methodology-vector11')}>
          При отсутствии событий или недоступности источника показываем «Нет данных». Сравниваем
          периоды одинаковой длины.
        </p>
      </Surface>
    </>
  );
}
