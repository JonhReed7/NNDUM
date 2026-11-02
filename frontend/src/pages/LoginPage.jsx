import { AuthLayout, AuthHeading, AuthActions } from '../components/AuthLayout.jsx';
import { AuthField } from '../components/AuthField.jsx';

export function LoginPage({ onSubmit, onGithub, onPasswordReset }) {
  function handleSubmit(event) {
    event.preventDefault();
    onSubmit?.(new FormData(event.currentTarget));
  }

  return (
    <AuthLayout mode="login">
      <AuthHeading
        eyebrow="С возвращением"
        title="Войдите в аккаунт"
        description="Следите за прогрессом вашей команды в одном месте"
      />
      <form onSubmit={handleSubmit}>
        <div className="fields fields--login">
          <AuthField label="Email" id="email" type="email" placeholder="name@company.ru" autoComplete="email" required />
          <AuthField label="Пароль" id="password" type="password" placeholder="Не менее 8 символов" autoComplete="current-password" minLength={8} required />
        </div>
        <div className="login-options">
          <label className="checkbox-label"><input type="checkbox" name="remember" />Запомнить меня</label>
          <button className="text-link" type="button" onClick={onPasswordReset}>Забыли пароль?</button>
        </div>
        <AuthActions mode="login" onGithub={onGithub} />
      </form>
      <p className="auth-footer">Нет аккаунта? <a href="#/register">Зарегистрироваться</a></p>
    </AuthLayout>
  );
}
