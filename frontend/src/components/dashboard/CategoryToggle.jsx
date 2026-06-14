function CategoryToggle({ options, activeValues, onToggle }) {
  return (
    <div className="toggle-row" role="group" aria-label="Trend lines">
      {options.map((item) => {
        const active = activeValues.includes(item.value);
        return (
          <button
            key={item.value}
            type="button"
            className={`button ${active ? "button--primary" : "button--secondary"}`}
            aria-pressed={active}
            onClick={() => onToggle(item.value)}
          >
            {item.label}
          </button>
        );
      })}
    </div>
  );
}

export default CategoryToggle;
