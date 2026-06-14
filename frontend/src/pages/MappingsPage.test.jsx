import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import MappingsPage from "./MappingsPage";

vi.mock("../features/mappings/KeywordMappingTab", () => ({
  default: () => <div>KeywordTabContent</div>
}));

vi.mock("../features/mappings/RegexMappingTab", () => ({
  default: () => <div>RegexTabContent</div>
}));

describe("MappingsPage", () => {
  it("switches between keyword and regex tabs", () => {
    render(<MappingsPage />);

    expect(screen.getByText("KeywordTabContent")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: /regex rules/i }));

    expect(screen.getByText("RegexTabContent")).toBeInTheDocument();
  });
});
