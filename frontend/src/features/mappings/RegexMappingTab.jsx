import { useMemo, useState } from "react";
import ErrorState from "../../components/ui/ErrorState";
import Skeleton from "../../components/ui/Skeleton";
import Table from "../../components/ui/Table";
import Toast from "../../components/ui/Toast";
import MappingCreateForm from "./MappingCreateForm";
import { useEnqueueReparse } from "./useEnqueueReparse";
import { useCreateRegexMapping, useRegexMappings } from "./useRegexMappings";

function RegexMappingTab() {
  const { data, isLoading, error, refetch } = useRegexMappings();
  const createMutation = useCreateRegexMapping();
  const reparseMutation = useEnqueueReparse();
  const [toast, setToast] = useState({ message: "", tone: "success" });
  const categories = Array.from(new Set((data || []).map((row) => String(row.category || "").trim().toLowerCase()).filter(Boolean)));

  const sortedRows = useMemo(() => {
    return [...(data || [])].sort((left, right) => Number(left.priority || 100) - Number(right.priority || 100));
  }, [data]);

  const handleCreate = async (payload) => {
    try {
      await createMutation.mutateAsync(payload);
      await reparseMutation.enqueue({ kind: "all" });
      setToast({ message: "Regex mapping added and transactions are being reclassified.", tone: "success" });
      return { ok: true };
    } catch (createError) {
      setToast({ message: createError.message || "Failed to create regex mapping.", tone: "error" });
      return { ok: false };
    }
  };

  return (
    <div className="stack">
      <Toast message={toast.message} tone={toast.tone} />
      {isLoading ? <Skeleton rows={4} /> : null}
      {error ? <ErrorState message={error.message || "Unable to load regex mappings."} onRetry={refetch} /> : null}
      {!isLoading && !error ? (
        <Table>
          <thead>
            <tr>
              <th scope="col">Name</th>
              <th scope="col">Pattern</th>
              <th scope="col">Category</th>
              <th scope="col">Priority</th>
            </tr>
          </thead>
          <tbody>
            {sortedRows.length ? (
              sortedRows.map((row) => (
                <tr key={row.id || `${row.name}-${row.pattern}`}>
                  <td>{row.name}</td>
                  <td>{row.pattern}</td>
                  <td>{row.category}</td>
                  <td>{row.priority ?? 100}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={4}>No regex mappings found.</td>
              </tr>
            )}
          </tbody>
        </Table>
      ) : null}
      <MappingCreateForm
        type="regex"
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

export default RegexMappingTab;
