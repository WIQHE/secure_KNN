import React, { useState } from 'react';
import OwnerView from './components/OwnerView.js';
import QueryView from './components/QueryView.js';

const ROLE_STORAGE_KEY = 'secureKnn.role';

function readRoleFromUrl() {
  try {
    const params = new URLSearchParams(window.location.search);
    const r = params.get('role');
    if (r === 'owner' || r === 'query') return r;
  } catch {}
  return null;
}

function readRole() {
  // URL param wins — lets two browser windows run different roles even when
  // they share localStorage. Falls back to localStorage so a refresh keeps you
  // in the role you picked from the landing screen.
  const fromUrl = readRoleFromUrl();
  if (fromUrl) return fromUrl;
  try { return sessionStorage.getItem(ROLE_STORAGE_KEY) || null; } catch { return null; }
}

export default function App() {
  const [role, setRole] = useState(readRole);

  const pickRole = (r) => {
    try { sessionStorage.setItem(ROLE_STORAGE_KEY, r); } catch {}
    setRole(r);
  };

  const switchRole = () => {
    try { sessionStorage.removeItem(ROLE_STORAGE_KEY); } catch {}
    // Also strip ?role=... so the picker reappears.
    try {
      const url = new URL(window.location.href);
      url.searchParams.delete('role');
      window.history.replaceState({}, '', url.toString());
    } catch {}
    setRole(null);
  };

  return (
    <div className="mt-4">
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h1 className="mb-0">Secure k-NN</h1>
        {role && (
          <button type="button" className="btn btn-outline-secondary btn-sm" onClick={switchRole}>
            Switch role ({role})
          </button>
        )}
      </div>

      {!role && (
        <div className="row g-3">
          <div className="col-md-6">
            <div className="card h-100">
              <div className="card-body">
                <h3 className="card-title">Data Owner</h3>
                <p className="card-text">
                  I have a dataset to publish. My browser will encrypt it under my secret key
                  and process incoming query re-encryption requests.
                </p>
                <button className="btn btn-primary" onClick={() => pickRole('owner')}>
                  Open Data Owner console
                </button>
              </div>
            </div>
          </div>
          <div className="col-md-6">
            <div className="card h-100">
              <div className="card-body">
                <h3 className="card-title">Query User</h3>
                <p className="card-text">
                  I want to query the encrypted dataset. My browser will encrypt the query,
                  wait for the Data Owner to co-encrypt it, then submit it to the cloud.
                </p>
                <button className="btn btn-primary" onClick={() => pickRole('query')}>
                  Open Query User console
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {role === 'owner' && <OwnerView />}
      {role === 'query' && <QueryView />}
    </div>
  );
}
