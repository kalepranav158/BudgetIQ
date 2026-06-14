const monthNames = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December"
];

const shortMonthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export function toYearMonthKey(year, month) {
  return `${year}-${String(month).padStart(2, "0")}`;
}

export function parseISODate(value) {
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

export function getMonthLabel(year, month, compact = false) {
  const index = Number(month) - 1;
  if (index < 0 || index > 11) {
    return `${month}/${year}`;
  }
  return compact ? `${shortMonthNames[index]} ${year}` : `${monthNames[index]} ${year}`;
}

export function sortByYearMonthDesc(rows) {
  return [...rows].sort((left, right) => Number(right.year) * 100 + Number(right.month) - (Number(left.year) * 100 + Number(left.month)));
}

export function sameYearMonth(inputDate, year, month) {
  const parsed = parseISODate(inputDate);
  if (!parsed) {
    return false;
  }
  return parsed.getFullYear() === Number(year) && parsed.getMonth() + 1 === Number(month);
}
