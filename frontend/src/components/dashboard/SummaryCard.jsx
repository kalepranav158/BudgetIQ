function SummaryCard({ label, value, tone = "default", subtitle = "" }) {
  return (
    <article className={`summary-card summary-card--${tone}`}>
      <h3 className="summary-card__label">{label}</h3>
      <p className="summary-card__value">{value}</p>
      {subtitle ? <p className="summary-card__subtitle">{subtitle}</p> : null}
    </article>
  );
}

export default SummaryCard;
