import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import MappingCreateForm from "./MappingCreateForm";

describe("MappingCreateForm", () => {
  it("validates required fields for keyword mappings", async () => {
    const onSubmit = vi.fn(async () => ({ ok: true }));
    render(<MappingCreateForm type="keyword" onSubmit={onSubmit} pending={false} />);

    fireEvent.click(screen.getByRole("button", { name: /add mapping/i }));

    expect(await screen.findByText("Keyword is required.")).toBeInTheDocument();
    expect(await screen.findByText("Please select a category.")).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits regex mapping payload when valid", async () => {
    const onSubmit = vi.fn(async () => ({ ok: true }));
    render(<MappingCreateForm type="regex" onSubmit={onSubmit} pending={false} />);

    fireEvent.change(screen.getByLabelText("Name"), { target: { value: "Food" } });
    fireEvent.change(screen.getByLabelText("Pattern"), { target: { value: "SWIGGY|ZOMATO" } });
    fireEvent.change(screen.getByLabelText("Category"), { target: { value: "lunch" } });
    fireEvent.change(screen.getByLabelText("Priority"), { target: { value: "2" } });
    fireEvent.click(screen.getByRole("button", { name: /add rule/i }));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({
        name: "Food",
        pattern: "SWIGGY|ZOMATO",
        category: "lunch",
        priority: "2"
      });
    });
  });
});
