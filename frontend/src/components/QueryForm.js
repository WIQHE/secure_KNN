export default function QueryForm({ onResult }) {
  const handleSubmit = async (e) => {
    e.preventDefault();
    const text = e.target.elements.vector.value.trim();
    const fileInput = e.target.elements.queryFile;
    let res;
    if (fileInput.files.length) {
      const formData = new FormData();
      formData.append('file', fileInput.files[0]);
      res = await fetch('/query', {
        method: 'POST',
        body: formData,
      });
    } else if (text) {
      const vector = text.split(',').map(Number);
      res = await fetch('/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ vector }),
      });
    } else {
      return;
    }
    const data = await res.json().catch(() => ({ message: 'Invalid JSON response' }));
    onResult(data);
  };

  return (
    <form onSubmit={handleSubmit} className="mb-4">
      <h2>Submit Query Vector</h2>
      <div className="mb-3">
        <label className="form-label">Enter vector (comma separated)</label>
        <textarea name="vector" className="form-control" rows="3"></textarea>
      </div>
      <div className="mb-3">
        <label className="form-label">Or upload vector file</label>
        <input type="file" name="queryFile" className="form-control" />
      </div>
      <button type="submit" className="btn btn-primary">Submit Query</button>
    </form>
  );
}
