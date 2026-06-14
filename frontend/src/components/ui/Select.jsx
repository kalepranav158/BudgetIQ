function Select({ id, label, error, children, ...props }) {
  return (
    <div className="field">
      <label className="field__label" htmlFor={id}>
        {label}
      </label>
      <select
        id={id}
        className={`field__control${error ? " field__control--error" : ""}`}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? `${id}-error` : undefined}
        {...props}
      >
        {children}
      </select>
      {error ? (
        <div className="field__error" id={`${id}-error`}>
          {error}
        </div>
      ) : null}
    </div>
  );
}

export default Select;
