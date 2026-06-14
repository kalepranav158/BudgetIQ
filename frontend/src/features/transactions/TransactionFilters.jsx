import Input from "../../components/ui/Input";
import Select from "../../components/ui/Select";
import { CATEGORIES } from "../../constants/categories";
import { SUBTYPES } from "../../constants/subtypes";

function TransactionFilters({ category, subtype, search, onCategoryChange, onSubtypeChange, onSearchChange }) {
  return (
    <div className="filters">
      <Select id="transaction-category" label="Category" value={category} onChange={(event) => onCategoryChange(event.target.value)}>
        <option value="all">All categories</option>
        {CATEGORIES.map((item) => (
          <option key={item} value={item}>
            {item}
          </option>
        ))}
      </Select>
      <Select id="transaction-subtype" label="Subtype" value={subtype} onChange={(event) => onSubtypeChange(event.target.value)}>
        <option value="all">All subtypes</option>
        {SUBTYPES.map((item) => (
          <option key={item} value={item}>
            {item}
          </option>
        ))}
      </Select>
      <Input id="transaction-search" label="Search description" value={search} onChange={(event) => onSearchChange(event.target.value)} placeholder="Search by description" />
    </div>
  );
}

export default TransactionFilters;
