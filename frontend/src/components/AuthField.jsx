import { useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';

export function AuthField({ label, id, type = 'text', error, className = '', ...props }) {
  const [visible, setVisible] = useState(false);
  const isPassword = type === 'password';
  const passwordLabel = label === 'Повторите пароль' ? 'повторный пароль' : label.toLowerCase();
  return (
    <div className={`field ${error ? 'field--error' : ''} ${className}`}>
      <label htmlFor={id}>{label}</label>
      <div className="field-control">
        <input
          id={id}
          name={id}
          type={isPassword && visible ? 'text' : type}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? `${id}-error` : undefined}
          {...props}
        />
        {isPassword && (
          <button
            className="password-toggle"
            type="button"
            aria-label={`${visible ? 'Скрыть' : 'Показать'} ${passwordLabel}`}
            aria-pressed={visible}
            onClick={() => setVisible(!visible)}
          >
            {visible ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
        )}
      </div>
      {error && <p className="field-error" id={`${id}-error`} role="alert">{error}</p>}
    </div>
  );
}
