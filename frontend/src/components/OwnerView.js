import React, { useEffect, useRef, useState, useCallback } from 'react';
import { generateSecrets, encryptDataset, doQueryStep2 } from '../crypto/aspe.js';
import { api } from '../api/client.js';

const SECRETS_STORAGE_KEY = 'secureKnn.ownerSecrets';
const MAXNORM_STORAGE_KEY = 'secureKnn.ownerMaxNorm';

function parseCsv(text) {
  return text
    .trim()
    .split(/\r?\n/)
    .filter((line) => line.trim().length > 0)
    .map((line) => line.split(',').map((cell) => Number(cell.trim())));
}

function loadStoredSecrets() {
  try {
    const raw = localStorage.getItem(SECRETS_STORAGE_KEY);
    const maxNorm = localStorage.getItem(MAXNORM_STORAGE_KEY);
    if (!raw) return null;
    const secrets = JSON.parse(raw);
    return { secrets, maxNorm: maxNorm ? Number(maxNorm) : null };
  } catch {
    return null;
  }
}

function persistSecrets(secrets, maxNorm) {
  localStorage.setItem(SECRETS_STORAGE_KEY, JSON.stringify(secrets));
  if (maxNorm !== null && maxNorm !== undefined) {
    localStorage.setItem(MAXNORM_STORAGE_KEY, String(maxNorm));
  }
}

function clearStoredSecrets() {
  localStorage.removeItem(SECRETS_STORAGE_KEY);
  localStorage.removeItem(MAXNORM_STORAGE_KEY);
}

function downloadJson(filename, payload) {
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export default function OwnerView() {
  const [secrets, setSecrets] = useState(() => loadStoredSecrets()?.secrets || null);
  const [maxNorm, setMaxNorm] = useState(() => loadStoredSecrets()?.maxNorm || null);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');
  const [pending, setPending] = useState([]);
  const [processed, setProcessed] = useState([]);
  const processingRef = useRef(new Set());

  // --- Dataset upload ---
  const handleDatasetSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setStatus('reading file…');
    const fileInput = e.target.elements.dataset;
    if (!fileInput.files.length) return;
    const text = await fileInput.files[0].text();
    const data = parseCsv(text);
    if (!data.length) {
      setError('CSV had no rows.');
      setStatus('');
      return;
    }
    const d = data[0].length;
    try {
      setStatus('generating secrets…');
      const newSecrets = generateSecrets({ d });
      setStatus('encrypting dataset client-side…');
      const { encData, maxNorm: mn } = encryptDataset(data, newSecrets);
      setStatus('uploading ciphertext to CSP…');
      const resp = await api.postDataset(encData);
      setSecrets(newSecrets);
      setMaxNorm(mn);
      persistSecrets(newSecrets, mn);
      setStatus(`dataset stored: n=${resp.n}, eta=${resp.eta}, max_norm=${mn.toFixed(3)}`);
    } catch (err) {
      console.error(err);
      setError(err.message || String(err));
      setStatus('');
    }
  };

  // --- Secret export / import / clear ---
  const handleExport = () => {
    if (!secrets) return;
    downloadJson('secure-knn-owner-secrets.json', { secrets, maxNorm });
  };

  const handleImport = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    try {
      const obj = JSON.parse(await file.text());
      if (!obj.secrets) throw new Error('file missing "secrets" key');
      setSecrets(obj.secrets);
      setMaxNorm(obj.maxNorm ?? null);
      persistSecrets(obj.secrets, obj.maxNorm ?? null);
      setStatus('secrets imported.');
      setError('');
    } catch (err) {
      setError(`import failed: ${err.message}`);
    }
  };

  const handleClear = () => {
    if (!window.confirm('Clear stored DO secrets from this browser?')) return;
    clearStoredSecrets();
    setSecrets(null);
    setMaxNorm(null);
    setStatus('secrets cleared.');
  };

  // --- Pending queries: poll + process ---
  const pollPending = useCallback(async () => {
    if (!secrets || maxNorm === null) return;
    try {
      const resp = await api.listPending();
      setPending(resp.pending || []);
      for (const item of resp.pending || []) {
        if (processingRef.current.has(item.query_id)) continue;
        processingRef.current.add(item.query_id);
        try {
          const { qHat, Mt } = doQueryStep2(item.q_dot, secrets, maxNorm);
          await api.postReencrypt(item.query_id, qHat, Mt);
          setProcessed((prev) => [
            { query_id: item.query_id, user_id: item.user_id, ts: new Date().toISOString() },
            ...prev,
          ].slice(0, 20));
        } catch (err) {
          console.error('re-encrypt failed', err);
          processingRef.current.delete(item.query_id);
        }
      }
    } catch (err) {
      // silent — server may be unreachable
    }
  }, [secrets, maxNorm]);

  useEffect(() => {
    if (!secrets) return undefined;
    pollPending();
    const id = setInterval(pollPending, 2000);
    return () => clearInterval(id);
  }, [secrets, pollPending]);

  return (
    <div>
      <h2>Data Owner</h2>
      <p className="text-muted">
        Encrypts the dataset client-side and re-encrypts incoming queries from query users.
        The server never sees plaintext data or DO secrets.
      </p>

      <section className="mb-4">
        <h4>1. Upload &amp; encrypt dataset</h4>
        <form onSubmit={handleDatasetSubmit} className="mb-2">
          <div className="mb-2">
            <input type="file" name="dataset" accept=".csv,text/csv" className="form-control" required />
          </div>
          <button type="submit" className="btn btn-primary">Encrypt &amp; upload</button>
        </form>
        {status && <div className="alert alert-info py-2 mb-2">{status}</div>}
        {error && <div className="alert alert-danger py-2 mb-2">{error}</div>}
      </section>

      <section className="mb-4">
        <h4>2. Secrets</h4>
        {secrets ? (
          <div>
            <div className="mb-2 text-success">
              ✓ Secrets in memory · eta={secrets.eta}, d={secrets.d}, c={secrets.c}, ep={secrets.ep}
              {maxNorm !== null && <> · max_norm={maxNorm.toFixed(3)}</>}
            </div>
            <button type="button" className="btn btn-outline-secondary btn-sm me-2" onClick={handleExport}>
              Download secrets JSON
            </button>
            <label className="btn btn-outline-secondary btn-sm me-2 mb-0">
              Import secrets…
              <input type="file" accept="application/json" hidden onChange={handleImport} />
            </label>
            <button type="button" className="btn btn-outline-danger btn-sm" onClick={handleClear}>
              Clear from browser
            </button>
          </div>
        ) : (
          <div className="text-muted">No DO secrets yet. Upload a dataset to generate them, or import from JSON:
            <label className="btn btn-outline-secondary btn-sm ms-2 mb-0">
              Import secrets…
              <input type="file" accept="application/json" hidden onChange={handleImport} />
            </label>
          </div>
        )}
      </section>

      <section className="mb-4">
        <h4>3. Pending query re-encryption</h4>
        {!secrets ? (
          <div className="text-muted">Upload a dataset first.</div>
        ) : (
          <>
            <div className="mb-2">Polling /query/pending every 2s · {pending.length} pending</div>
            <h6>Recently processed</h6>
            {processed.length === 0 ? (
              <div className="text-muted">none yet</div>
            ) : (
              <ul className="list-group">
                {processed.map((p) => (
                  <li key={p.query_id} className="list-group-item small">
                    {p.ts} — {p.user_id} — {p.query_id}
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
      </section>
    </div>
  );
}
