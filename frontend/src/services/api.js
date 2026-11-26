const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL?.trim() || 'https://nndum.onrender.com'
).replace(/\/+$/, '');

const AUTH_STORAGE_KEY = 'devpulse.auth';
const AUTH_STORAGES = ['sessionStorage', 'localStorage'];

let tabSession;

function isAuthSession(data) {
  return typeof data?.access_token === 'string' && data.access_token.trim() !== '' &&
    typeof data.user?.id === 'string' && data.user.id.trim() !== '' &&
    [data.token_type, data.user.email, data.user.first_name, data.user.last_name, data.user.username].every(
      (value) => value == null || typeof value === 'string',
    );
}

function isExpiredToken(token) {
  const parts = token.split('.');
  if (parts.length !== 3) return false;

  try {
    const payload = JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')));
    return typeof payload?.exp === 'number' && payload.exp * 1000 <= Date.now();
  } catch {
    return false;
  }
}

function getErrorMessage(action, status, detail) {
  if (status >= 500) return 'Сервис временно недоступен. Попробуйте позже.';
  if (action.endsWith('/url')) return 'Не удалось начать вход через OAuth. Попробуйте ещё раз.';
  if (action.endsWith('/callback')) return 'Не удалось подтвердить вход через OAuth. Начните вход заново.';
  if (status === 401 && action === 'login') return 'Неверный адрес электронной почты или пароль.';
  if (action === 'register' && status === 400 && detail === 'User with this email already exists') {
    return 'Аккаунт с таким адресом электронной почты уже существует.';
  }
  if (status === 422) return 'Проверьте введённые данные.';

  return action === 'login'
    ? 'Не удалось войти. Попробуйте ещё раз.'
    : 'Не удалось зарегистрироваться. Попробуйте ещё раз.';
}

async function requestAuthData(action, options) {
  let response;
  let data;

  try {
    response = await fetch(`${API_BASE_URL}/auth/${action}`, options);
    data = await response.json().catch((error) => {
      if (error instanceof SyntaxError) return null;
      throw error;
    });
  } catch (error) {
    if (options.signal?.aborted || error?.name === 'AbortError') throw error;
    throw new Error('Не удалось связаться с сервером. Проверьте подключение и попробуйте ещё раз.');
  }

  if (!response.ok) {
    throw new Error(getErrorMessage(action, response.status, data?.detail));
  }

  return data;
}

async function requestAuth(action, credentials, signal) {
  const data = await requestAuthData(action, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(credentials),
    signal,
  });

  if (!isAuthSession(data)) {
    throw new Error('Сервер вернул неполные данные для входа. Попробуйте ещё раз.');
  }

  const { id, email, first_name, last_name, username } = data.user;
  return {
    access_token: data.access_token,
    token_type: data.token_type ?? 'bearer',
    user: { id, email, first_name, last_name, username },
  };
}

export function login(credentials, signal) {
  return requestAuth('login', credentials, signal);
}

export function register(credentials, signal) {
  return requestAuth('register', credentials, signal);
}

function oauthAction(provider, action) {
  if (provider !== 'github' && provider !== 'google') {
    throw new Error('Этот способ входа недоступен.');
  }
  return `${provider}/${action}`;
}

export async function getOAuthUrl(provider, signal) {
  const data = await requestAuthData(oauthAction(provider, 'url'), { redirect: 'error', signal });
  return data?.url;
}

export async function completeOAuth(provider, code, signal) {
  return requestAuth(oauthAction(provider, 'callback'), { code }, signal);
}

export function getAuthSession() {
  if (tabSession !== undefined) {
    return tabSession && !isExpiredToken(tabSession.access_token) ? tabSession : null;
  }

  for (const storageName of AUTH_STORAGES) {
    try {
      const session = JSON.parse(window[storageName].getItem(AUTH_STORAGE_KEY));
      if (isAuthSession(session) && !isExpiredToken(session.access_token)) return session;
    } catch {
      continue;
    }
  }

  return null;
}

export function saveAuthSession(session, remember = false) {
  clearAuthSession();
  tabSession = session;
  const storageName = remember ? 'localStorage' : 'sessionStorage';

  try {
    window[storageName].setItem(AUTH_STORAGE_KEY, JSON.stringify(session));
  } catch {
    // Keep the session in this tab when browser storage is unavailable.
  }
}

export function clearAuthSession() {
  tabSession = null;

  for (const storageName of AUTH_STORAGES) {
    try {
      window[storageName].removeItem(AUTH_STORAGE_KEY);
    } catch {
      continue;
    }
  }
}
