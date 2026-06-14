import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import HealthCard from "./HealthCard";

describe("HealthCard", () => {
  it("renders offline status and error details", () => {
    render(
      <HealthCard
        serviceName="FastAPI"
        url="http://127.0.0.1:8001/health"
        data={{ online: false, checkedAt: "2026-04-02T00:00:00.000Z", message: "Offline" }}
      />
    );

    expect(screen.getByText("FastAPI")).toBeInTheDocument();
    expect(screen.getAllByText("Offline").length).toBeGreaterThan(0);
    expect(screen.getByText(/Last checked:/)).toBeInTheDocument();
  });
});
