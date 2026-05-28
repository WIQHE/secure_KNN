import React, { useEffect, useRef, useState } from 'react';
import { quQueryStep1, quQueryStep3 } from '../crypto/aspe.js';
import { api } from '../api/client.js';

const USER_ID_STORAGE_KEY = 'secureKnn.queryUserId';

function loadUserId() {
  try {
    return localStorage.getItem(USER_ID_STORAGE_KEY) || `qu-${Math.random().toString(36).slice(2, 8)}`;
  } catch {
    return `qu-${Math.random().toString(36).slice(2, 8)}`;
  }
}

function parseVector(text) {
  return text
    .trim()
    .split(',')
    .map((cell) => Number(cell.trim()))
    .filter((v) => !Number.isNaN(v));
}

export default function QueryView() {
  const [userId, setUserId] = useState(loadUserId);
  const [vectorText, setVectorText] = useState('');
  const [k, setK] = useState(3);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const pendingRef = useRef(null); // {queryId, Nvalues, eta?, beta1}

  useEffect(() => {
    try { localStorage.setItem(USER_ID_STORAGE_KEY, userId); } catch {}
  }, [userId]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setResult(null);
    const q = parseVector(vectorText);
    if (!q.length) {
      setError('enter a comma-separated query vector');
      return;
    }
    try {
      setStatus('QU step 1: encrypting query…');
      const { qDot, Nvalues } = quQueryStep1(q);
      const submitResp = await api.submitQuery(userId, qDot);
      pendingRef.current = { queryId: submitResp.query_id, Nvalues };
      setStatus(`submitted (query_id=${submitResp.query_id}). Waiting for DO re-encryption…`);
    } catch (err) {
      console.error(err);
      setError(err.message || String(err));
      setStatus('');
    }
  };

  // Poll for re-encrypted result.
  useEffect(() => {
    if (!pendingRef.current) return undefined;
    const id = setInterval(async () => {
      const ctx = pendingRef.current;
      if (!ctx) return;
      try {
        const resp = await api.fetchReencrypted(ctx.queryId);
        if (!resp.ready) return;
        // q_hat received — perform QU step 3.
        const qHat = resp.q_hat;
        const eta = qHat.length;
        const { qTildeVec } = quQueryStep3(qHat, ctx.Nvalues, eta);
        setStatus('QU step 3: removing N-layer, finalizing on CSP…');
        const fin = await api.finalize(ctx.queryId, qTildeVec, Number(k) || 3);
        setStatus(`done — result_id=${fin.result_id}`);
        setResult(fin);
        setHistory((prev) => [
          { ts: new Date().toISOString(), queryId: ctx.queryId, indices: fin.indices },
          ...prev,
        ].slice(0, 10));
        pendingRef.current = null;
        clearInterval(id);
      } catch (err) {
        console.error('poll/finalize failed', err);
        setError(err.message || String(err));
        pendingRef.current = null;
        clearInterval(id);
      }
    }, 2000);
    return () => clearInterval(id);
  }, [status, k]);

  return (
    <div>
      <h2>Query User</h2>
      <p className="text-muted">
        Encrypts the query client-side (step 1), waits for the DO to re-encrypt (step 2),
        removes its own layer (step 3), and forwards to the CSP for k-NN computation.
      </p>

      <section className="mb-4">
        <h4>Identity</h4>
        <div className="input-group" style={{ maxWidth: 360 }}>
          <span className="input-group-text">user_id</span>
          <input
            className="form-control"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
          />
        </div>
      </section>

      <section className="mb-4">
        <h4>Submit query</h4>
        <form onSubmit={handleSubmit}>
          <div className="mb-2">
            <label className="form-label">Query vector (comma-separated, length d)</label>
            <textarea
              className="form-control"
              rows="2"
              value={vectorText}
              onChange={(e) => setVectorText(e.target.value)}
              placeholder="e.g. 12, 34, 56, 78, 90, 11, 22, 33"
            />
          </div>
          <div className="mb-2" style={{ maxWidth: 160 }}>
            <label className="form-label">k</label>
            <input
              type="number"
              className="form-control"
              min="1"
              value={k}
              onChange={(e) => setK(e.target.value)}
            />
          </div>
          <button type="submit" className="btn btn-primary">Encrypt &amp; submit</button>
        </form>
      </section>

      {status && <div className="alert alert-info py-2">{status}</div>}
      {error && <div className="alert alert-danger py-2">{error}</div>}

      {result && (
        <section className="mb-4">
          <h4>Result</h4>
          <pre className="bg-light p-3">{JSON.stringify(result, null, 2)}</pre>
        </section>
      )}

      {history.length > 0 && (
        <section className="mb-4">
          <h4>Recent queries</h4>
          <ul className="list-group">
            {history.map((h) => (
              <li key={h.queryId} className="list-group-item small">
                {h.ts} — [{h.indices.join(', ')}] — {h.queryId}
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
