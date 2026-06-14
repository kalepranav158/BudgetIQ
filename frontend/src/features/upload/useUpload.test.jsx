import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("./useUpload", () => ({
  useUpload: () => ({
    mutateAsync: vi.fn(),
    isPending: false
  })
}));

import UploadForm from "./UploadForm";

describe("UploadForm", () => {
  it("shows a validation error when no file is selected", async () => {
    render(<UploadForm />);

    fireEvent.click(screen.getByRole("button", { name: /upload/i }));

    expect(await screen.findByText("Please select a PDF file.")).toBeInTheDocument();
  });
});
