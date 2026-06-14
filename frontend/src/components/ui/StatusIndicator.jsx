function StatusIndicator({ online }) {
  return (
    <span className={`status-indicator${online ? " status-indicator--online" : " status-indicator--offline"}`}>
      <span className="status-indicator__dot" aria-hidden="true" />
      <span>{online ? "Online" : "Offline"}</span>
    </span>
  );
}

export default StatusIndicator;
