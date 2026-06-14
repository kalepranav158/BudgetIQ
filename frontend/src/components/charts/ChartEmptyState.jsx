function ChartEmptyState({ message = "No data available for this period." }) {
  return <div className="chart-empty">{message}</div>;
}

export default ChartEmptyState;
