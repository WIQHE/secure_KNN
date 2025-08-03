import DatasetForm from './components/DatasetForm.js';
import QueryForm from './components/QueryForm.js';
import ResultsPanel from './components/ResultsPanel.js';

const { useState } = React;

export default function App() {
  const [datasetResult, setDatasetResult] = useState(null);
  const [queryResult, setQueryResult] = useState(null);

  return (
    <div className="mt-4">
      <h1 className="mb-4">Secure KNN Interface</h1>
      <DatasetForm onResult={setDatasetResult} />
      <QueryForm onResult={setQueryResult} />
      <ResultsPanel datasetResult={datasetResult} queryResult={queryResult} />
    </div>
  );
}
