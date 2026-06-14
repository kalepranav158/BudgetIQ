import { DEBIT_CATEGORIES } from "../constants/categoryColors";
import { parseISODate, toYearMonthKey } from "./dateHelpers";

function toNumber(value) {
  const parsed = Number.parseFloat(value ?? 0);
  return Number.isFinite(parsed) ? parsed : 0;
}

export function computeCategoryTotals(rows) {
  return DEBIT_CATEGORIES.reduce((acc, category) => {
    acc[category] = rows.reduce((sum, row) => sum + toNumber(row?.[category]), 0);
    return acc;
  }, {});
}

export function computeMonthSummary(rows) {
  const debit = rows.reduce((sum, row) => sum + toNumber(row?.total_debit), 0);
  const credit = rows.reduce((sum, row) => sum + toNumber(row?.credit ?? row?.total_credit), 0);
  const categoryTotals = computeCategoryTotals(rows);

  let topCategory = { name: "other", amount: 0 };
  for (const category of DEBIT_CATEGORIES) {
    const amount = categoryTotals[category] || 0;
    if (amount > topCategory.amount) {
      topCategory = { name: category, amount };
    }
  }

  return {
    debit,
    credit,
    net: credit - debit,
    topCategory,
    categoryTotals
  };
}

export function aggregateByMonth(dailyRows) {
  const map = new Map();

  for (const row of dailyRows || []) {
    const date = parseISODate(row?.date);
    if (!date) {
      continue;
    }

    const year = date.getFullYear();
    const month = date.getMonth() + 1;
    const key = toYearMonthKey(year, month);

    if (!map.has(key)) {
      map.set(key, {
        year,
        month,
        total_debit: 0,
        total_credit: 0,
        ...DEBIT_CATEGORIES.reduce((acc, category) => {
          acc[category] = 0;
          return acc;
        }, {})
      });
    }

    const current = map.get(key);
    current.total_debit += toNumber(row?.total_debit);
    current.total_credit += toNumber(row?.credit ?? row?.total_credit);

    for (const category of DEBIT_CATEGORIES) {
      current[category] += toNumber(row?.[category]);
    }
  }

  return Array.from(map.values()).sort((left, right) => Number(left.year) * 100 + Number(left.month) - (Number(right.year) * 100 + Number(right.month)));
}

export function computeSubtypeTotals(transactions) {
  const totals = {};
  for (const tx of transactions || []) {
    const subtype = tx?.subtype || "unknown";
    const amount = toNumber(tx?.amount);
    totals[subtype] = (totals[subtype] || 0) + amount;
  }
  return totals;
}

export function topSpendingDays(rows, limit = 5) {
  return [...(rows || [])]
    .sort((left, right) => toNumber(right?.total_debit) - toNumber(left?.total_debit))
    .slice(0, limit);
}
