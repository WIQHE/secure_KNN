// Tiny fetch wrapper for the CSP server endpoints.

async function jsonReq(url, options = {}) {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  const text = await res.text();
  let body = null;
  try {
    body = text ? JSON.parse(text) : null;
  } catch {
    body = { error: 'invalid JSON response', raw: text };
  }
  if (!res.ok) {
    const msg = (body && body.error) || `HTTP ${res.status}`;
    const err = new Error(msg);
    err.status = res.status;
    err.body = body;
    throw err;
  }
  return body;
}

export const api = {
  postDataset: (encData) =>
    jsonReq('/dataset', { method: 'POST', body: JSON.stringify({ enc_data: encData }) }),

  submitQuery: (userId, qDot) =>
    jsonReq('/query/submit', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, q_dot: qDot }),
    }),

  listPending: () => jsonReq('/query/pending'),

  postReencrypt: (queryId, qHat, mT) =>
    jsonReq('/query/reencrypt', {
      method: 'POST',
      body: JSON.stringify({ query_id: queryId, q_hat: qHat, m_t: mT }),
    }),

  fetchReencrypted: (queryId) => jsonReq(`/query/${queryId}/reencrypted`),

  finalize: (queryId, qTildeVec, k) =>
    jsonReq(`/query/${queryId}/finalize`, {
      method: 'POST',
      body: JSON.stringify({ q_tilde_vec: qTildeVec, k }),
    }),

  fetchResult: (resultId) => jsonReq(`/results/${resultId}`),

  health: () => jsonReq('/health'),
};
