import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import ForecastTrendChart from "./ForecastTrendChart";

const forecastRows = [
  {
    date: "2026-04-15",
    predicted_total_debit: 510,
    lower_bound: 470,
    upper_bound: 550,
  },
  {
    date: "2026-04-16",
    predicted_total_debit: 530,
    lower_bound: 480,
    upper_bound: 570,
  },
];

const recentActualRows = [
  {
    date: "2026-04-14",
    actual_total_debit: 490,
  },
];

describe("ForecastTrendChart", () => {
  it("calls toggle handlers from interactive legend", () => {
    const onToggleForecast = vi.fn();
    const onToggleBand = vi.fn();
    const onToggleActualOverlay = vi.fn();

    render(
      <ForecastTrendChart
        rows={forecastRows}
        recentActualRows={recentActualRows}
        showForecast={true}
        showBand={true}
        showActualOverlay={true}
        onToggleForecast={onToggleForecast}
        onToggleBand={onToggleBand}
        onToggleActualOverlay={onToggleActualOverlay}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /forecast/i }));
    fireEvent.click(screen.getByRole("button", { name: /confidence band/i }));
    fireEvent.click(screen.getByRole("button", { name: /actual overlay/i }));

    expect(onToggleForecast).toHaveBeenCalledTimes(1);
    expect(onToggleBand).toHaveBeenCalledTimes(1);
    expect(onToggleActualOverlay).toHaveBeenCalledTimes(1);
  });

  it("disables actual overlay legend button when no actual rows are available", () => {
    render(
      <ForecastTrendChart
        rows={forecastRows}
        recentActualRows={[]}
        showForecast={true}
        showBand={true}
        showActualOverlay={false}
      />,
    );

    const actualOverlayButton = screen.getByRole("button", { name: /actual overlay/i });
    expect(actualOverlayButton).toBeDisabled();
  });
});