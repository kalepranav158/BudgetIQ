import StatusIndicator from "../../components/ui/StatusIndicator";

function HealthCard({ serviceName, url, data }) {
  return (
    <article className="health-card">
      <h2 className="health-card__title">{serviceName}</h2>
      <p className="health-card__url">{url}</p>
      <StatusIndicator online={data.online} />
      <p className="health-card__checked">
        Last checked: {data.checkedAt ? new Date(data.checkedAt).toLocaleString() : "Never"}
      </p>
      {!data.online && data.message ? <p className="health-card__error">{data.message}</p> : null}
    </article>
  );
}

export default HealthCard;
