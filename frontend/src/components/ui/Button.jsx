function Button({ children, type = "button", variant = "primary", loading = false, ...props }) {
  return (
    <button type={type} className={`button button--${variant}`} disabled={loading || props.disabled} {...props}>
      {loading ? "Loading..." : children}
    </button>
  );
}

export default Button;
