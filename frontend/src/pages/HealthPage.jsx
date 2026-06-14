import HealthCard from "../features/health/HealthCard";
import { useHealthStatus } from "../features/health/useHealthStatus";
import { DJANGO_TARGET_URL, FASTAPI_TARGET_URL } from "../constants/api";

function HealthPage() {
  const { django, fastapi, isLoading } = useHealthStatus();

  return (
    <section className="page">
      <h1 className="page-title">Health</h1>
      <p className="page-subtitle">Check Django and FastAPI service status.</p>
      {isLoading ? <p>Checking service status...</p> : null}
      <div className="health-grid">
        <HealthCard serviceName="Django" url={`${DJANGO_TARGET_URL}/health`} data={django || { online: false, checkedAt: null }} />
        <HealthCard serviceName="FastAPI" url={`${FASTAPI_TARGET_URL}/health`} data={fastapi || { online: false, checkedAt: null }} />
      </div>
    </section>
  );
}

export default HealthPage;
