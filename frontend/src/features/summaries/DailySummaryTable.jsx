import Table from "../../components/ui/Table";
import { CATEGORIES } from "../../constants/categories";

const summaryColumns = ["cash_withdrawal", "extra", "lunch", "other", "recharge", "tea", "credit"];

function DailySummaryTable({ rows }) {
  const maxDebit = rows.reduce((max, row) => Math.max(max, Number(row.total_debit || 0)), 0) || 1;
  const maxCredit = rows.reduce((max, row) => Math.max(max, Number(row.total_credit || 0)), 0) || 1;

  return (
    <Table>
      <thead>
        <tr>
          <th scope="col">Date</th>
          {CATEGORIES.map((category) => (
            <th scope="col" key={category}>{category}</th>
          ))}
          <th scope="col">Total Debit (viz)</th>
          <th scope="col">Total Credit (viz)</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row.date}>
            <td>{row.date}</td>
            {summaryColumns.map((column) => (
              <td key={column}>{row[column] ?? "0.00"}</td>
            ))}
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

export default DailySummaryTable;
