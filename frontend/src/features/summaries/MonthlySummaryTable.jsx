import Table from "../../components/ui/Table";

function formatMonth(value) {
  if (typeof value === "string" && value.trim()) {
    return value;
  }
  return String(value ?? "");
}

function MonthlySummaryTable({ rows }) {
  const maxDebit = rows.reduce((max, row) => Math.max(max, Number(row.total_debit || 0)), 0) || 1;
  const maxCredit = rows.reduce((max, row) => Math.max(max, Number(row.total_credit || 0)), 0) || 1;

  return (
    <Table>
      <thead>
        <tr>
          <th scope="col">Month</th>
          <th scope="col">Total Debit (viz)</th>
          <th scope="col">Total Credit (viz)</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={`${row.year}-${row.month}`}>
            <td>{formatMonth(row.label || `${row.month} ${row.year}`)}</td>
            <td className="viz-cell">
              <div>{row.total_debit ?? "0.00"}</div>
              <div className="viz-track">
                <div className="viz-fill viz-fill--debit" style={{ width: `${(Number(row.total_debit || 0) / maxDebit) * 100}%` }} />
              </div>
            </td>
            <td className="viz-cell">
              <div>{row.total_credit ?? "0.00"}</div>
              <div className="viz-track">
                <div className="viz-fill viz-fill--credit" style={{ width: `${(Number(row.total_credit || 0) / maxCredit) * 100}%` }} />
              </div>
            </td>
          </tr>
        ))}
      </tbody>
    </Table>
  );
}

export default MonthlySummaryTable;
