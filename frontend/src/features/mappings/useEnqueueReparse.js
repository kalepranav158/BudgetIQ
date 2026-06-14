import { useState } from "react";
import { postUrlEncoded, getDjango } from "../../lib/apiClient";

export function useEnqueueReparse() {
  const [status, setStatus] = useState(null);
  const [progress, setProgress] = useState(0);
  const [jobId, setJobId] = useState(null);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [lastRunAt, setLastRunAt] = useState(null);

  async function enqueue(payload) {
    setError(null);
    setResult(null);
    setLastRunAt(null);
    setStatus("queued");
    const res = await postUrlEncoded("/reparse-mapping/enqueue", payload);
    const jid = res.job_id;
    setJobId(jid);
    poll(jid);
    return jid;
  }

  async function poll(jid) {
    try {
      setStatus("running");
      while (true) {
        const s = await getDjango(`/reparse-mapping/status/${jid}`);
        setStatus(s.status);
        setProgress(s.progress || 0);
        if (s.status === "done" || s.status === "failed") {
          if (s.status === "failed") {
            setError(s.error || "failed");
          } else {
            setResult(s.result || null);
            setLastRunAt(s.updated_at || null);
          }
          break;
        }
        await new Promise((r) => setTimeout(r, 1500));
      }
    } catch (err) {
      setError(err.message || String(err));
      setStatus("failed");
    }
  }

  return { enqueue, status, progress, jobId, error, result, lastRunAt };
}
