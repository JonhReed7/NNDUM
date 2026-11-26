import { getOAuthUrl } from './api.js';

export { completeOAuth } from './api.js';

const AUTHORIZATION_URLS = {
  github: 'https://github.com/login/oauth/authorize',
  google: 'https://accounts.google.com/o/oauth2/v2/auth',
};
const STATE_MAX_AGE = 15 * 60 * 1000;

function appBasePath() {
  const { pathname } = new URL(import.meta.env.BASE_URL, window.location.origin);
  return pathname.endsWith('/') ? pathname : `${pathname}/`;
}

function callbackProvider(path, basePath) {
  if (!path.startsWith(basePath)) return undefined;
  return /^auth\/(github|google)(?:\/callback)?\/?$/.exec(path.slice(basePath.length))?.[1];
}

export async function startOAuth(provider, mode, remember, signal) {
  const url = await getOAuthUrl(provider, signal);
  let authorization;
  let callback;

  try {
    authorization = new URL(url);
    const destinations = authorization.searchParams.getAll('redirect_uri');
    callback = new URL(destinations.length === 1 ? destinations[0] : '');
  } catch {
    throw new Error('Сервер вернул некорректную ссылку для входа.');
  }

  if (
    `${authorization.origin}${authorization.pathname}` !== AUTHORIZATION_URLS[provider] ||
    authorization.username || authorization.password || authorization.hash
  ) {
    throw new Error('Сервер вернул некорректную ссылку для входа.');
  }

  if (
    callback.origin !== window.location.origin || callbackProvider(callback.pathname, appBasePath()) !== provider ||
    callback.username || callback.password || callback.search || callback.hash
  ) {
    throw new Error('Адрес возврата после входа не совпадает с адресом сайта.');
  }

  signal?.throwIfAborted();
  const state = window.crypto.randomUUID();

  try {
    window.sessionStorage.setItem(`devpulse.oauth.${provider}`, JSON.stringify({
      state,
      mode: mode === 'register' ? 'register' : 'login',
      remember: Boolean(remember),
      createdAt: Date.now(),
    }));
  } catch {
    throw new Error('Разрешите сайту сохранять данные в браузере и попробуйте войти снова.');
  }

  authorization.searchParams.set('state', state);
  window.location.assign(authorization.href);
}

export function consumeOAuthCallback() {
  const basePath = appBasePath();
  const provider = callbackProvider(window.location.pathname, basePath);
  if (!provider) return null;

  const query = new URLSearchParams(window.location.search);
  const states = query.getAll('state');
  const key = `devpulse.oauth.${provider}`;
  let mode = 'login';
  let attempt;

  try {
    const stored = JSON.parse(window.sessionStorage.getItem(key));
    if (stored?.mode === 'register') mode = 'register';
    if (states.length === 1 && states[0] && stored?.state === states[0]) {
      window.sessionStorage.removeItem(key);
      attempt = stored;
    }
  } catch {
    // A callback without readable, one-time state cannot be accepted.
  }

  window.history.replaceState(window.history.state, '', `${basePath}#/${mode}`);

  if (!Number.isFinite(attempt?.createdAt) || Date.now() - attempt.createdAt > STATE_MAX_AGE) {
    return { mode, error: 'Не удалось проверить запрос на вход. Начните вход заново.' };
  }

  if (query.has('error')) {
    const error = query.get('error') === 'access_denied'
      ? 'Вход через OAuth отменён.'
      : 'Сервис авторизации вернул ошибку. Попробуйте ещё раз.';
    return { mode, error };
  }

  const codes = query.getAll('code');
  if (codes.length !== 1 || !codes[0].trim()) {
    return { mode, error: 'Сервис авторизации не вернул код для входа. Попробуйте ещё раз.' };
  }

  return { provider, mode, remember: attempt.remember === true, code: codes[0] };
}
