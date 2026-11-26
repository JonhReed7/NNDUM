import { useState } from 'react';
import { AuthLayout, AuthHeading, AuthActions } from '../components/AuthLayout.jsx';
import { AuthField } from '../components/AuthField.jsx';
import { useAuthSubmit } from '../hooks/useAuthSubmit.js';

export function RegisterPage({ onSubmit, onTerms, callbackError, callbackPending }) {
  const { error, pending, submit } = useAuthSubmit(callbackError);
  const [password, setPassword] = useState('');
  const [repeat, setRepeat] = useState('');
  const [repeatTouched, setRepeatTouched] = useState(false);
  const mismatch = password !== repeat && (repeatTouched || Boolean(repeat));

  function handleSubmit(event) {
    event.preventDefault();
    if (callbackPending) return;
    setRepeatTouched(true);
    if (password !== repeat) return;
    const formData = new FormData(event.currentTarget);
    submit('email', (signal) => onSubmit?.(formData, signal));
  }

  return (
    <AuthLayout mode="register">
      <AuthHeading
        eyebrow="Начните работу"
        title="Создайте аккаунт"
        description="Подключите GitHub и получите первый отчёт"
      />
      <form onSubmit={handleSubmit}>
        <div className="fields fields--register">
          <div className="name-fields">
            <AuthField label="Имя" id="firstName" placeholder="Иван" autoComplete="given-name" maxLength={100} required />
            <AuthField label="Фамилия" id="lastName" placeholder="Иванов" autoComplete="family-name" maxLength={100} required />
          </div>
          <AuthField label="Имя пользователя" id="username" placeholder="Иван123" autoComplete="username" minLength={2} maxLength={64} required />
          <AuthField label="Email" id="email" type="email" placeholder="name@company.ru" autoComplete="email" required />
          <AuthField label="Пароль" id="password" type="password" placeholder="Не менее 8 символов" autoComplete="new-password" minLength={8} maxLength={128} value={password} onChange={(event) => setPassword(event.target.value)} required />
          <AuthField label="Повторите пароль" id="passwordConfirmation" type="password" placeholder="Повторите пароль" autoComplete="new-password" minLength={8} maxLength={128} value={repeat} onChange={(event) => setRepeat(event.target.value)} onBlur={() => setRepeatTouched(true)} error={mismatch ? 'Пароли не совпадают' : undefined} required />
        </div>
        <label className="checkbox-label terms">
          <input type="checkbox" name="terms" required />
          <span>Я согласен с <button type="button" className="text-link" onClick={onTerms}>условиями использования</button></span>
        </label>
        <AuthActions mode="register" error={error} pending={callbackPending ? 'callback' : pending} submit={submit} />
      </form>
      <p className="auth-footer">Уже есть аккаунт? <a href="#/login">Войти</a></p>
    </AuthLayout>
  );
}
