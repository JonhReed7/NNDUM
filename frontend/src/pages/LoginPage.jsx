import { AuthLayout, AuthHeading, AuthActions } from '../components/AuthLayout.jsx';
import { AuthField } from '../components/AuthField.jsx';
import { useAuthSubmit } from '../hooks/useAuthSubmit.js';

export function LoginPage({ onSubmit, onPasswordReset, onDemo, callbackError, callbackPending }) {
  const { error, pending, submit } = useAuthSubmit(callbackError);

  function handleSubmit(event) {
    event.preventDefault();
    if (callbackPending) return;
    const formData = new FormData(event.currentTarget);
    submit('email', (signal) => onSubmit?.(formData, signal));
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
          <AuthField label="Пароль" id="password" type="password" placeholder="Не менее 8 символов" autoComplete="current-password" minLength={8} maxLength={128} required />
        </div>
        <div className="login-options">
          <label className="checkbox-label"><input type="checkbox" name="remember" />Запомнить меня</label>
          <button className="text-link" type="button" onClick={onPasswordReset}>Забыли пароль?</button>
        </div>
        <AuthActions mode="login" error={error} pending={callbackPending ? 'callback' : pending} submit={submit} />
      </form>
      <p className="auth-footer">Нет аккаунта? <a href="#/register">Зарегистрироваться</a></p>
      {onDemo && <p className="demo-entry"><button type="button" className="text-link" onClick={onDemo}>Посмотреть демо без входа</button></p>}
    </AuthLayout>
  );
}
