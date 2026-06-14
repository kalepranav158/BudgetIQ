import ErrorState from "../../components/ui/ErrorState";
import Skeleton from "../../components/ui/Skeleton";
import Table from "../../components/ui/Table";
import Toast from "../../components/ui/Toast";
import MappingCreateForm from "./MappingCreateForm";
import { useEnqueueReparse } from "./useEnqueueReparse";
import { useCreateKeywordMapping, useKeywordMappings } from "./useKeywordMappings";
import { useState } from "react";

function KeywordMappingTab() {
  const { data, isLoading, error, refetch } = useKeywordMappings();
  const createMutation = useCreateKeywordMapping();
  const reparseMutation = useEnqueueReparse();
  const [toast, setToast] = useState({ message: "", tone: "success" });
  const categories = Array.from(new Set((data || []).map((row) => String(row.category || "").trim().toLowerCase()).filter(Boolean)));

  const handleCreate = async (payload) => {
    try {
      await createMutation.mutateAsync(payload);
      await reparseMutation.enqueue({ kind: "all" });
      setToast({ message: "Keyword mapping added and transactions are being reclassified.", tone: "success" });
      return { ok: true };
    } catch (createError) {
      setToast({ message: createError.message || "Failed to create keyword mapping.", tone: "error" });
      return { ok: false };
    }
  };

  return (
    <div className="stack">
      <Toast message={toast.message} tone={toast.tone} />
      {isLoading ? <Skeleton rows={4} /> : null}
      {error ? <ErrorState message={error.message || "Unable to load keyword mappings."} onRetry={refetch} /> : null}
      {!isLoading && !error ? (
        <Table>
          <thead>
            <tr>
              <th scope="col">Keyword</th>
              <th scope="col">Category</th>
            </tr>
          </thead>
          <tbody>
            {data?.length ? (
              data.map((row) => (
                <tr key={`${row.keyword}-${row.category}`}>
                  <td>{row.keyword}</td>
                  <td>{row.category}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={2}>No keyword mappings found.</td>
              </tr>
            )}
          </tbody>
        </Table>
      ) : null}
      <MappingCreateForm
        type="keyword"
        onSubmit={handleCreate}
        pending={createMutation.isPending}
        categories={categories}
      />
      {reparseMutation.status ? (
        <div className="stack">
          <strong>Reclassify status</strong>
          <div>Status: {reparseMutation.status}</div>
          <div>Progress: {reparseMutation.progress}%</div>
          {reparseMutation.error ? <div style={{ color: "var(--danger-600)" }}>{reparseMutation.error}</div> : null}
        </div>
      ) : null}
    </div>
  );
}

export default KeywordMappingTab;
