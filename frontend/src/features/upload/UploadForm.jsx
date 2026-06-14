import { useState } from "react";
import Button from "../../components/ui/Button";
import FileInput from "../../components/ui/FileInput";
import Input from "../../components/ui/Input";
import { useUpload } from "./useUpload";

function UploadForm({ onSuccess }) {
  const uploadMutation = useUpload();
  const [file, setFile] = useState(null);
  const [password, setPassword] = useState("");
  const [fileError, setFileError] = useState("");
  const [submitError, setSubmitError] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!file) {
      setFileError("Please select a PDF file.");
      setSubmitError("");
      return;
    }

    setFileError("");
    setSubmitError("");
    try {
      const result = await uploadMutation.mutateAsync({ file, password });
      setFile(null);
      setPassword("");
      onSuccess?.(result);
    } catch (mutationError) {
      setSubmitError(mutationError.message || "Upload failed");
    }
  };

  return (
    <form className="stack" onSubmit={handleSubmit}>
      <FileInput
        id="statement-file"
        label="Statement PDF"
        accept=".pdf"
        onChange={(event) => {
          setFile(event.target.files?.[0] || null);
          setFileError("");
        }}
        error={fileError}
      />
      <Input
        id="statement-password"
        label="PDF password"
        type="password"
        placeholder="PDF password (if any)"
        value={password}
        onChange={(event) => setPassword(event.target.value)}
      />
      {submitError ? <div className="field__error">{submitError}</div> : null}
      <Button type="submit" loading={uploadMutation.isPending}>
        Upload
      </Button>
    </form>
  );
}

export default UploadForm;
