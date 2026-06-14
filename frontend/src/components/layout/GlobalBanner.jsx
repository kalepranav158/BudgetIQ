function GlobalBanner({ message }) {
  if (!message) {
    return null;
  }

  return <div className="global-banner">{message}</div>;
}

export default GlobalBanner;
