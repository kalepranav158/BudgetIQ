function Input({ id, label, error, ...props }) {
  return (
    <div className="field">
      <label className="field__label" htmlFor={id}>
        {label}
      </label>
      <input
        id={id}
        className={`field__control${error ? " field__control--error" : ""}`}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? `${id}-error` : undefined}
        {...props}
      />
      {error ? (
        <div className="field__error" id={`${id}-error`}>
          {error}
        </div>
      ) : null}
    </div>
  );
}

export default Input;
