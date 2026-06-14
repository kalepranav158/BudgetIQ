import { useEffect, useMemo, useState } from "react";
import ErrorState from "../../components/ui/ErrorState";
import Skeleton from "../../components/ui/Skeleton";
import { SUBTYPES } from "../../constants/subtypes";
import TransactionFilters from "./TransactionFilters";
import TransactionTable from "./TransactionTable";
import { useTransactions } from "./useTransactions";

const PAGE_SIZE = 50;

function toTime(value) {
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? 0 : parsed.getTime();
}

function TransactionsView() {
  const { data, isLoading, error, refetch } = useTransactions();
  const [category, setCategory] = useState("all");
  const [subtype, setSubtype] = useState("all");
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState("date");
  const [sortDirection, setSortDirection] = useState("desc");
  const [page, setPage] = useState(1);

  const rows = useMemo(() => {
    const filtered = (data || []).filter((row) => {
      const matchesCategory = category === "all" || row.category === category;
      const matchesSubtype = subtype === "all" || row.subtype === subtype;
      const matchesSearch = !search || String(row.description || "").toLowerCase().includes(search.toLowerCase());
      return matchesCategory && matchesSubtype && matchesSearch;
    });

    filtered.sort((left, right) => {
      const direction = sortDirection === "asc" ? 1 : -1;
      if (sortKey === "amount") {
        return (Number(left.amount) - Number(right.amount)) * direction;
      }
      return (toTime(left.date) - toTime(right.date)) * direction;
    });

    return filtered;
  }, [category, data, search, sortDirection, sortKey, subtype]);

  useEffect(() => {
    setPage(1);
  }, [category, search, sortDirection, sortKey, subtype]);

  const totalPages = Math.max(1, Math.ceil(rows.length / PAGE_SIZE));
  const pageRows = rows.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const toggleSort = (column) => {
    if (sortKey === column) {
      setSortDirection((current) => (current === "asc" ? "desc" : "asc"));
      return;
    }
    setSortKey(column);
    setSortDirection(column === "date" ? "desc" : "asc");
  };

  if (isLoading) {
    return <Skeleton rows={5} />;
  }

  if (error) {
    return <ErrorState message={error.message || "Unable to load transactions."} onRetry={refetch} />;
  }

  return (
    <div className="stack">
      <TransactionFilters
        category={category}
        subtype={subtype}
        search={search}
        onCategoryChange={setCategory}
        onSubtypeChange={setSubtype}
        onSearchChange={setSearch}
      />
      {pageRows.length === 0 ? (
        <p>No transactions found. Upload a statement to get started.</p>
      ) : (
        <TransactionTable rows={pageRows} sortKey={sortKey} sortDirection={sortDirection} onSort={toggleSort} />
      )}
      <div className="pagination">
        <button className="button button--secondary" type="button" onClick={() => setPage((current) => Math.max(1, current - 1))} disabled={page === 1}>
          Previous
        </button>
        <span>
          Page {page} of {totalPages}
        </span>
        <button className="button button--secondary" type="button" onClick={() => setPage((current) => Math.min(totalPages, current + 1))} disabled={page >= totalPages}>
          Next
        </button>
      </div>
      <p>Subtype options: {SUBTYPES.join(", ")}</p>
    </div>
  );
}

export default TransactionsView;
