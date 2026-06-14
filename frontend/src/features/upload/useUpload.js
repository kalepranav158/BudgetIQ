import { useMutation } from "@tanstack/react-query";
import { DJANGO_BASE_URL } from "../../constants/api";
import { postForm } from "../../lib/apiClient";

async function uploadPdf({ file, password }) {
  const formData = new FormData();
  formData.append("file", file);
  if (password) {
    formData.append("password", password);
  }
  return postForm(DJANGO_BASE_URL, "/upload-pdf", formData, { timeout: 180000 });
}

export function useUpload() {
  return useMutation({
    mutationFn: uploadPdf
  });
}
