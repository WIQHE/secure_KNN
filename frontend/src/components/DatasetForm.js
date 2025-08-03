export default function DatasetForm({ onResult }) {
  const handleSubmit = async (e) => {
    e.preventDefault();
    const fileInput = e.target.elements.dataset;
    if (!fileInput.files.length) return;
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    const res = await fetch('/dataset', {
      method: 'POST',
      body: formData,
    });
    const data = await res.json().catch(() => ({ message: 'Invalid JSON response' }));
    onResult(data);
  };

  return (
    <form onSubmit={handleSubmit} className="mb-4">
      <h2>Upload Dataset</h2>
      <div className="mb-3">
        <input type="file" name="dataset" className="form-control" required />
      </div>
      <button type="submit" className="btn btn-primary">Upload Dataset</button>
    </form>
  );
}
