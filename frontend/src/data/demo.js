// Shared demo data keeps the dashboard, report and exports in sync.
export const initialTeams = [
  {
    id: 'alpha',
    name: 'Команда Альфа',
    reportName: 'Команда «Альфа»',
    role: 'Владелец',
    projects: '4 проекта',
    members: ['АК', 'МП', 'ЕС'],
    tone: 'blue',
  },
  {
    id: 'product',
    name: 'Продуктовая команда',
    role: 'Участник',
    projects: '2 проекта',
    members: ['ИВ', 'ОЛ', 'ДК'],
    tone: 'cyan',
  },
  {
    id: 'mobile',
    name: 'Mobile Core',
    role: 'Участник',
    projects: '1 проект',
    members: ['НС', 'АМ'],
    tone: 'violet',
  },
];

export const projects = [
  {
    id: 'marketplace',
    name: 'Marketplace Web',
    repository: 'acme/marketplace-web',
    teamId: 'alpha',
    lastAnalysis: 'Сегодня, 10:42',
    status: 'ready',
  },
  {
    id: 'mobile',
    name: 'Mobile App',
    repository: 'acme/mobile-app',
    teamId: 'mobile',
    lastAnalysis: 'Сегодня, 09:18',
    status: 'processing',
  },
  {
    id: 'analytics',
    name: 'Analytics API',
    repository: 'acme/analytics-api',
    teamId: 'product',
    lastAnalysis: '12 мая, 18:30',
    status: 'ready',
  },
];

export const defaultAnalysis = {
  teamId: 'alpha',
  repository: 'https://example.com/alpha/marketplace-web',
  branch: 'main',
  commit: '8a31b7c',
  startDate: '2026-10-12',
  endDate: '2026-11-01',
  projectName: 'Marketplace Web',
};

export const metrics = [
  {
    name: 'Активные участники',
    value: '4 из 4',
    note: '100% команды',
    formula: 'Доля участников с коммитом, PR или комментарием за спринт.',
    source: 'Git + API',
  },
  {
    name: 'Первый отклик на PR',
    value: '9 ч',
    note: 'Было 14 ч',
    formula: 'Медиана до первого ответа коллеги после открытия PR.',
    source: 'API платформы',
  },
  {
    name: 'PR с ревью',
    value: '82%',
    note: '9 из 11 PR',
    formula: 'Доля слитых PR, проверенных коллегой до слияния.',
    source: 'API платформы',
  },
  {
    name: 'Зависшие ветки',
    value: '2',
    note: 'Было 3 ветки',
    formula: 'Открытые ветки без новых коммитов больше 7 дней.',
    source: 'Git + API',
  },
  {
    name: 'Осмысленные сообщения',
    value: '88%',
    formula: 'Доля сообщений коммитов, которые проходят формальную проверку.',
    source: 'Git',
  },
  {
    name: 'Распределение изменений',
    value: '36% / 29% / 22% / 13%',
    formula: 'Доли изменённых символов по авторам без сгенерированных файлов.',
    source: 'Git',
  },
  {
    name: 'Полнота README',
    value: '4 из 4',
    formula: 'Проверка назначения проекта, установки, запуска и структуры.',
    source: 'Снимок Git',
  },
  {
    name: 'Чистота репозитория',
    value: '0 файлов',
    formula: 'Число отслеживаемых файлов из списка исключений.',
    source: 'Снимок Git',
  },
];

export const contributors = [
  { name: 'Анна', commits: 32, prs: 4, reviews: 3 },
  { name: 'Максим', commits: 26, prs: 3, reviews: 4 },
  { name: 'Илья', commits: 19, prs: 3, reviews: 2 },
  { name: 'София', commits: 11, prs: 1, reviews: 2 },
];

export function formatPeriod(analysis, short = false) {
  const months = [
    'янв',
    'фев',
    'мар',
    'апр',
    'мая',
    'июн',
    'июл',
    'авг',
    'сен',
    'окт',
    'ноя',
    'дек',
  ];
  if (short) {
    const compactDate = (value) => {
      const [, month, day] = value.split('-').map(Number);
      return `${day} ${months[month - 1]}`;
    };
    return `${compactDate(analysis.startDate)} — ${compactDate(analysis.endDate)}`;
  }
  const options = { day: 'numeric', month: 'long', timeZone: 'UTC' };
  const start = new Date(`${analysis.startDate}T00:00:00Z`).toLocaleDateString('ru-RU', options);
  const end = new Date(`${analysis.endDate}T00:00:00Z`).toLocaleDateString('ru-RU', options);
  return `${start} — ${end} ${analysis.endDate.slice(0, 4)}`;
}
