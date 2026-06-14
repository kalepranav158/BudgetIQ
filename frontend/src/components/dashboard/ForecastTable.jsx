import { formatCurrency } from "../../utils/formatCurrency";
import Table from "../ui/Table";

function ForecastTable({ rows }) {
  return (
    <Table>
      <thead>
        <tr>
          <th scope="col">Date</th>
          <th scope="col">Predicted Debit</th>
          <th scope="col">Lower Bound</th>
          <th scope="col">Upper Bound</th>
        </tr>
      </thead>
      <tbody>
        {(rows || []).map((row) => (
          <tr key={row.date}>
            <td>{row.date}</td>
            <td>{formatCurrency(row.predicted_total_debit)}</td>
            <td>{formatCurrency(row.lower_bound)}</td>
            <td>{formatCurrency(row.upper_bound)}</td>
          </tr>
        ))}
      </tbody>
    </Table>
  );
}

export default ForecastTable;