import { useEffect, useRef, useState } from 'react';
import { PageHeading, Surface, WorkspaceButton } from '../components/WorkspaceUI.jsx';
import { artwork } from '../assets/figma.js';

const stages = [
  'Проверка доступа и хэша',
  'Сбор коммитов и ревью',
  'Расчёт метрик',
  'Формирование отчёта',
];

export function AnalysisPage({ analysis, teams, onStart }) {
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const timer = useRef(null);
  useEffect(() => () => clearTimeout(timer.current), []);

  function submit(event) {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(event.currentTarget));
    if (data.startDate > data.endDate) {
      setError('Конец периода не может быть раньше начала.');
      return;
    }
    setError('');
    setBusy(true);
    // This is explicitly a demo transition, not a simulated server request.
    timer.current = setTimeout(() => onStart({ ...analysis, ...data }), 500);
  }

  return (
    <>
      <PageHeading
        title="Новый анализ"
        description="Подключите репозиторий и выберите период"
        projectName={analysis.projectName}
      />
      <div className="analysis-grid">
        <Surface art="analysis-vector9" className="analysis-parameters">
          <h2>Параметры репозитория</h2>
          <p className="section-description">Выберите команду для расчёта</p>
          <form onSubmit={submit} aria-busy={busy} onChange={() => setError('')}>
            <fieldset disabled={busy} className="analysis-fields">
              <label className="workspace-field">
                Команда
                <select
                  name="teamId"
                  defaultValue={analysis.teamId}
                  style={artwork('analysis-vector11')}
                  required
                >
                  {teams.map((team) => (
                    <option key={team.id} value={team.id}>
                      {team.name}
                    </option>
                  ))}
                </select>
              </label>
              <label className="workspace-field">
                URL репозитория
                <input
                  name="repository"
                  type="url"
                  pattern="https?://.+"
                  defaultValue={analysis.repository}
                  style={artwork('analysis-vector11')}
                  required
                />
              </label>
              <div className="analysis-field-row">
                <label className="workspace-field">
                  Ветка
                  <input
                    name="branch"
                    defaultValue={analysis.branch}
                    style={artwork('analysis-vector12')}
                    required
                    maxLength={200}
                    pattern=".*\S.*"
                  />
                </label>
                <label className="workspace-field">
                  Хэш коммита · необязательно
                  <input
                    name="commit"
                    defaultValue={analysis.commit}
                    style={artwork('analysis-vector13')}
                    pattern="[a-fA-F0-9]{7,40}"
                    title="От 7 до 40 шестнадцатеричных символов"
                    maxLength={40}
                  />
                </label>
              </div>
              <div className="analysis-field-row">
                <label className="workspace-field">
                  Начало периода
                  <input
                    name="startDate"
                    type="date"
                    defaultValue={analysis.startDate}
                    style={artwork('analysis-vector12')}
                    required
                  />
                </label>
                <label className="workspace-field">
                  Конец периода
                  <input
                    name="endDate"
                    type="date"
                    defaultValue={analysis.endDate}
                    style={artwork('analysis-vector13')}
                    required
                    aria-invalid={Boolean(error)}
                    aria-describedby={error ? 'period-error' : undefined}
                  />
                </label>
              </div>
            </fieldset>
            {error && (
              <p id="period-error" className="workspace-error" role="alert">
                {error}
              </p>
            )}
            <WorkspaceButton
              type="submit"
              art="analysis-vector14"
              className="start-analysis"
              disabled={busy}
            >
              {busy ? 'Открываем пример…' : 'Запустить анализ'}
            </WorkspaceButton>
            <span className="sr-only" role="status">
              {busy ? 'Открываем демонстрационный дашборд. Серверный анализ не выполняется.' : ''}
            </span>
          </form>
        </Surface>
        <Surface art="analysis-vector10" className="analysis-stages">
          <h2>Этапы анализа</h2>
          <p className="section-description">Автоматический сбор и расчёт</p>
          <ol>
            {stages.map((stage, index) => (
              <li key={stage}>
                <span style={artwork('analysis-vector15')} aria-hidden="true">
                  {index + 1}
                </span>
                {stage}
              </li>
            ))}
          </ol>
          <p className="section-description">Результат откроется на дашборде.</p>
          {busy && (
            <p className="demo-progress" role="status">
              Демо-режим: показываем пример отчёта.
            </p>
          )}
        </Surface>
      </div>
    </>
  );
}
