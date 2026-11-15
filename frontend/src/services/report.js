import { formatPeriod, metrics } from '../data/demo.js';

export function downloadReportCsv(analysis, teamName) {
  const escape = (value) => {
    const text = String(value);
    const safe = /^[=+\-@\t\r\n]/.test(text) ? `'${text}` : text;
    return `"${safe.replace(/"/g, '""')}"`;
  };
  const rows = [
    ['DevPulse — демонстрационный отчёт'],
    ['Проект', analysis.projectName],
    ['Команда', teamName],
    ['Период', formatPeriod(analysis)],
    ['Ветка', analysis.branch],
    ['Хэш снимка', analysis.commit || 'Не указан'],
    ['Часовой пояс', 'UTC+5'],
    [],
    ['Метрика', 'Значение'],
    ...metrics.map((metric) => [metric.name, metric.value]),
  ];
  const csv = '\uFEFF' + rows.map((row) => row.map(escape).join(';')).join('\r\n');
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8;' }));
  const link = document.createElement('a');
  link.href = url;
  link.download = `devpulse-report-${analysis.startDate}-${analysis.endDate}.csv`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
