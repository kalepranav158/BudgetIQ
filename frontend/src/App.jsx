import { useMemo } from "react";
import AppShell from "./components/layout/AppShell";
import GlobalBanner from "./components/layout/GlobalBanner";
import AppRoutes from "./routes";
import { useHealthStatus } from "./features/health/useHealthStatus";

function App() {
  const { fastapi, isLoading } = useHealthStatus();

  const bannerMessage = useMemo(() => {
    if (isLoading || fastapi?.online) {
      return "";
    }
    return "Parser service is not responding. PDF uploads will fail.";
  }, [fastapi?.online, isLoading]);

  return (
    <AppShell>
      {bannerMessage ? <GlobalBanner message={bannerMessage} /> : null}
      <AppRoutes />
    </AppShell>
  );
}

export default App;
