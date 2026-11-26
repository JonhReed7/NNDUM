import { Github } from 'lucide-react';
import googleIcon from '../assets/figma/auth-google.svg';
import { startOAuth } from '../services/oauth.js';
import { PromoPanel } from './PromoPanel.jsx';

export function AuthLayout({ mode, children }) {
  return (
    <main className={`auth-page auth-page--${mode}`}>
      <PromoPanel />
      <section className="form-panel" aria-labelledby="auth-title">
        <div className="auth-content">{children}</div>
      </section>
    </main>
  );
}

export function AuthHeading({ eyebrow, title, description }) {
  return (
    <header className="auth-heading">
      <p className="eyebrow">{eyebrow}</p>
      <h1 id="auth-title">{title}</h1>
      <p className="auth-description">{description}</p>
    </header>
  );
}

export function AuthActions({ mode, error, pending, submit }) {
  const registration = mode === 'register';
  const submitLabel = registration ? 'Зарегистрироваться' : 'Войти';
  const pendingLabel = registration ? 'Регистрируем…' : 'Выполняем вход…';
  const busy = Boolean(pending);

  function signInWith(provider, form) {
    if (busy) return;
    const remember = form.elements.namedItem('remember')?.checked ?? false;
    submit(provider, (signal) => startOAuth(provider, mode, remember, signal));
  }

  return (
    <div className="auth-actions">
      {error && <p className="field-error" role="alert">{error}</p>}
      {pending === 'callback' && <p className="auth-status" role="status">Завершаем вход…</p>}
      <button className="button button--primary" type="submit" disabled={busy}>
        {pending === 'email' ? pendingLabel : submitLabel}
      </button>
      <div className="divider"><span>или</span></div>
      <div className="auth-providers">
        <button
          className="button button--github"
          type="button"
          disabled={busy}
          onClick={(event) => signInWith('github', event.currentTarget.form)}
        >
          <Github size={20} strokeWidth={1.8} aria-hidden="true" />
          {pending === 'github' ? 'Переходим в GitHub…' : `${submitLabel} через GitHub`}
        </button>
        <button
          className="button button--google"
          type="button"
          disabled={busy}
          onClick={(event) => signInWith('google', event.currentTarget.form)}
        >
          <img src={googleIcon} alt="" />
          {pending === 'google' ? 'Переходим в Google…' : `${submitLabel} через Google`}
        </button>
      </div>
    </div>
  );
}
