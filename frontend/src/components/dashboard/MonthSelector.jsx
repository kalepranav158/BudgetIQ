import { getMonthLabel } from "../../utils/dateHelpers";

function MonthSelector({ options, selected, onChange }) {
  const value = selected ? `${selected.year}-${selected.month}` : "";

  return (
    <div className="month-selector">
      <label htmlFor="dashboard-month">Month</label>
      <select
        id="dashboard-month"
        value={value}
        onChange={(event) => {
          const [year, month] = event.target.value.split("-");
          if (!year || !month) {
            return;
          }
          onChange({ year: Number(year), month: Number(month) });
        }}
      >
        {options.map((item) => (
          <option key={`${item.year}-${item.month}`} value={`${item.year}-${item.month}`}>
            {getMonthLabel(item.year, item.month)}
          </option>
        ))}
      </select>
    </div>
  );
}

export default MonthSelector;
