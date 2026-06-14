function UploadResultCard({ result }) {
  if (!result) {
    return null;
  }

  return (
    <section className="result-card">
      <h2>Upload complete</h2>
      <p>{result.saved_transactions ?? 0} transactions saved.</p>
      {Array.isArray(result.summaries) && result.summaries.length > 0 ? (
        <div className="result-card__summaries">
          <h3>Summary preview</h3>
          <pre>{JSON.stringify(result.summaries.slice(0, 3), null, 2)}</pre>
        </div>
      ) : null}
    </section>
  );
}

export default UploadResultCard;
