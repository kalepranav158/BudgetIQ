import Table from "../ui/Table";
import { DEBIT_CATEGORIES } from "../../constants/categoryColors";
import { formatCurrency } from "../../utils/formatCurrency";

function TopSpendingDaysTable({ rows }) {
  return (
    <Table>
      <thead>
        <tr>
          <th scope="col">Date</th>
          <th scope="col">Total Debit</th>
          {DEBIT_CATEGORIES.map((category) => (
            <th scope="col" key={category}>{category}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {(rows || []).map((row) => (
          <tr key={row.date}>
            <td>{row.date}</td>
            <td>{formatCurrency(row.total_debit)}</td>
            {DEBIT_CATEGORIES.map((category) => (
              <td key={category}>{formatCurrency(row[category] || 0)}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </Table>
  );
}

export default TopSpendingDaysTable;
