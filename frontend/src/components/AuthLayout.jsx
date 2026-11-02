import { Github } from 'lucide-react';
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

export function AuthActions({ mode, onGithub }) {
  const registration = mode === 'register';
  return (
    <div className="auth-actions">
      <button className="button button--primary" type="submit">
        {registration ? 'Зарегистрироваться' : 'Войти'}
      </button>
      <div className="divider"><span>или</span></div>
      <button className="button button--github" type="button" onClick={onGithub}>
        <Github size={20} strokeWidth={1.8} aria-hidden="true" />
        {registration ? 'Зарегистрироваться через GitHub' : 'Войти через GitHub'}
      </button>
    </div>
  );
}
