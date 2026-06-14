import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mutateAsync = vi.fn();

vi.mock("./useUpload", () => ({
  useUpload: () => ({
    mutateAsync,
    isPending: false
  })
}));

import UploadForm from "./UploadForm";

describe("UploadForm", () => {
  beforeEach(() => {
    mutateAsync.mockReset();
  });

  it("shows required file error when no file is selected", async () => {
    render(<UploadForm />);
    fireEvent.click(screen.getByRole("button", { name: /upload/i }));
    expect(await screen.findByText("Please select a PDF file.")).toBeInTheDocument();
  });

  it("shows API error from mutation failure", async () => {
    mutateAsync.mockRejectedValueOnce(new Error("Bad password"));
    render(<UploadForm />);

    const file = new File(["dummy"], "sample.pdf", { type: "application/pdf" });
    fireEvent.change(screen.getByLabelText("Statement PDF"), { target: { files: [file] } });
    fireEvent.change(screen.getByLabelText("PDF password"), { target: { value: "wrong" } });
    fireEvent.click(screen.getByRole("button", { name: /upload/i }));

    expect(await screen.findByText("Bad password")).toBeInTheDocument();
  });
});
