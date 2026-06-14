import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Table from "../../components/ui/Table";

function formatConfidence(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return "-";
  }
  return number.toFixed(2);
}

function TransactionTable({ rows, sortKey, sortDirection, onSort }) {
  return (
    <Table>
      <thead>
        <tr>
          <th scope="col">
            <Button variant="secondary" onClick={() => onSort("date")}>Date {sortKey === "date" ? `(${sortDirection})` : ""}</Button>
          </th>
          <th scope="col">Description</th>
          <th scope="col">
            <Button variant="secondary" onClick={() => onSort("amount")}>Amount {sortKey === "amount" ? `(${sortDirection})` : ""}</Button>
          </th>
          <th scope="col">Type</th>
          <th scope="col">Subtype</th>
          <th scope="col">Category</th>
          <th scope="col">Category Source</th>
          <th scope="col">Confidence</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row.id || `${row.date}-${row.description}-${row.amount}`}>
            <td>{row.date}</td>
            <td>{row.description}</td>
            <td>{row.amount}</td>
            <td>{row.type}</td>
            <td><Badge tone="default">{row.subtype}</Badge></td>
            <td><Badge tone="default">{row.category}</Badge></td>
            <td><Badge tone="default">{row.category_source || "-"}</Badge></td>
            <td>{formatConfidence(row.confidence)}</td>
          </tr>
        ))}
      </tbody>
    </Table>
  );
}

export default TransactionTable;
