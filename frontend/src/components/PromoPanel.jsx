export function Brand() {
  return (
    <a className="brand" href="#/login" aria-label="DevPulse — вход">
      <span className="brand-mark" aria-hidden="true">
        <span /><span /><span />
      </span>
      <span>DevPulse</span>
    </a>
  );
}

export function PromoPanel() {
  return (
    <aside className="promo" aria-label="О DevPulse">
      <div className="promo-orb" aria-hidden="true" />
      <svg className="promo-trend" viewBox="0 0 640 640" fill="none" aria-hidden="true">
        <path d="M175 500H277C370 500 417 334 520 334H680M430 480H680" />
        <circle cx="520" cy="334" r="8" />
      </svg>
      <Brand />
      <div className="promo-copy">
        <h2>Команда растёт,<br />когда видит прогресс</h2>
        <p>Аналитика разработки без ручных отчётов</p>
        <div className="chart-card" role="img" aria-label="Скорость команды выросла на 18 процентов">
          <div className="chart-heading">
            <span>Скорость команды</span>
            <strong>+18%</strong>
          </div>
          <div className="chart-bars" aria-hidden="true">
            {[48, 68, 56, 90, 80, 110, 96].map((height, index) => (
              <span key={index} style={{ '--bar-height': `${height}px` }} />
            ))}
          </div>
        </div>
      </div>
    </aside>
  );
}
