import { useState } from "react";
import UploadForm from "../features/upload/UploadForm";
import UploadResultCard from "../features/upload/UploadResultCard";

function UploadPage() {
  const [result, setResult] = useState(null);

  return (
    <section className="page">
      <h1 className="page-title">Upload Statement</h1>
      <p className="page-subtitle">Upload an SBI statement PDF to parse and classify transactions.</p>
      <UploadForm onSuccess={setResult} />
      <UploadResultCard result={result} />
    </section>
  );
}

export default UploadPage;
