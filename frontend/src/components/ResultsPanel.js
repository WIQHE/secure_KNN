export default function ResultsPanel({ datasetResult, queryResult }) {
  return (
    <div className="mb-4">
      <h2>Results</h2>
      <div className="mb-3">
        <h5>Dataset Response</h5>
        <pre>{datasetResult ? JSON.stringify(datasetResult, null, 2) : 'No dataset uploaded yet.'}</pre>
      </div>
      <div>
        <h5>Query Response</h5>
        <pre>{queryResult ? JSON.stringify(queryResult, null, 2) : 'No query submitted yet.'}</pre>
      </div>
    </div>
  );
}
