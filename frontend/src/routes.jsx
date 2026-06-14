import { Suspense, lazy } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

const DashboardPage = lazy(() => import("./pages/DashboardPage"));
const UploadPage = lazy(() => import("./pages/UploadPage"));
const TransactionsPage = lazy(() => import("./pages/TransactionsPage"));
const DailySummaryPage = lazy(() => import("./pages/DailySummaryPage"));
const MonthlySummaryPage = lazy(() => import("./pages/MonthlySummaryPage"));
const MappingsPage = lazy(() => import("./pages/MappingsPage"));
const HealthPage = lazy(() => import("./pages/HealthPage"));

function AppRoutes() {
  return (
    <Suspense fallback={<div className="page">Loading page...</div>}>
      <Routes>
        <Route path="/" element={<Navigate to="/upload" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/trends" element={<Navigate to="/dashboard" replace />} />
        <Route path="/daily" element={<Navigate to="/dashboard" replace />} />
        <Route path="/breakdown" element={<Navigate to="/dashboard" replace />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/transactions" element={<TransactionsPage />} />
        <Route path="/summaries/daily" element={<DailySummaryPage />} />
        <Route path="/summaries/monthly" element={<MonthlySummaryPage />} />
        <Route path="/mappings" element={<MappingsPage />} />
        <Route path="/health" element={<HealthPage />} />
      </Routes>
    </Suspense>
  );
}

export default AppRoutes;
