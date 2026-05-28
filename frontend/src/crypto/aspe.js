// ASPE (Asymmetric Scalar-Product-Preserving Encryption) — JS port of the
// scheme in SecureNN-ICISS-2023.pdf §5.
//
// Notation matches the paper:
//   d   = original data dimension
//   c   = security parameter (length of w / x / r^(q))
//   ep  = security parameter (length of z / 0^ep)
//   eta = d + 1 + c + ep
//   s   = (d+1)-length shifting vector  (DO long-term secret)
//   Mbase = eta x eta invertible matrix (DO long-term secret)
//   w   = c-length fixed vector         (DO long-term secret)
//   N   = d x d diagonal matrix         (QU per-query secret)
//   beta_1, beta_2 = real scalars       (per-query secrets)
//
// All matrices are nested JS arrays. We never use the permutation pi from
// the paper — Mbase already absorbs that randomness.

import {
  randInt,
  randIntMatrix,
  randIntVector,
  randUniformMatrix,
  zeros,
  diag,
  matMul,
  matInv,
  det,
  scalarMul,
  add,
  rowSum,
  vectorMax,
  vectorNormSquared,
  maxRowNorm,
  concat,
  toPlain,
} from './linalg.js';

// ----- Data Owner: key generation -------------------------------------------

export function generateSecrets({ d, c = 5, ep = 3 } = {}) {
  const eta = d + 1 + c + ep;
  // Mbase: integer-valued and invertible.
  let Mbase;
  for (let attempt = 0; attempt < 32; attempt++) {
    Mbase = randIntMatrix(eta, eta, 0, 100);
    if (Math.abs(det(Mbase)) > 1e-9) break;
  }
  const s = randIntVector(d + 1, 0, 10);
  const w = randIntVector(c, 0, 10);
  return { d, c, ep, eta, s, Mbase, w };
}

// ----- Data Owner: dataset encryption ---------------------------------------
// Per paper §5 Data Encryption:
//   p_tilde_i = (s_1 - 2 p_i1, ..., s_d - 2 p_id, s_{d+1} + ||p_i||^2, w, z_i)
//   p_prime_i = p_tilde_i . Mbase^{-1}

export function encryptDataset(data, secrets) {
  const { d, c, ep, eta, s, Mbase, w } = secrets;
  if (!data.length) throw new Error('empty dataset');
  if (data[0].length !== d) {
    throw new Error(`dataset width ${data[0].length} != d ${d}`);
  }
  const MbaseInv = toPlain(matInv(Mbase));
  const encRows = [];
  for (const row of data) {
    const shifted = new Array(d);
    let normSq = 0;
    for (let j = 0; j < d; j++) {
      shifted[j] = s[j] - 2 * row[j];
      normSq += row[j] * row[j];
    }
    const pDplus1 = s[d] + normSq;
    const z = randIntVector(ep, 0, 100);
    const pTilde = concat(shifted, [pDplus1], w, z);
    const pPrime = toPlain(matMul([pTilde], MbaseInv))[0];
    encRows.push(pPrime);
  }
  const maxNorm = maxRowNorm(data);
  return { encData: encRows, maxNorm };
}

// ----- Query User: step 1 ----------------------------------------------------
// q_dot = beta_1 * q * N  (paper §5 step 1)
//
// NOTE: the paper's Lemma 1 proof has an algebra error. Expanding p̃_i · q''_η
// gives β1·(s·q − 2·p_i·q) + s_{d+1} + ||p_i||² + w·x, NOT
//        β1·(s·q + s_{d+1} − 2·p_i·q + ||p_i||²) + w·x  as written.
// β1 only multiplies the dot-product terms because q''_η[d+1] = 1 (not β1).
// As a result the scheme is monotone in ||p_i − q||² only when β1 = 1; with
// random β1 ∈ [1,10) the ||p_i||² and p_i·q terms are mis-weighted and k-NN
// returns the wrong answers on within-cluster (small-D²) queries. We force
// β1 = 1 here. Security still relies on N (per-query diagonal secret).
export function quQueryStep1(q) {
  const d = q.length;
  const beta1 = 1;
  const Nvalues = randIntVector(d, 1, 10);
  const qDot = new Array(d);
  for (let j = 0; j < d; j++) qDot[j] = beta1 * q[j] * Nvalues[j];
  return { qDot, Nvalues, beta1 };
}

// ----- Data Owner: step 2 ----------------------------------------------------
// q_max = max(q_dot)
// M_t: eta x eta; diagonal > max_norm, off-diagonal > q_max
// M_sec = M_t . M_base
// q_prime = (q_dot, 1, x, 0^ep) packed into a diagonal matrix q_eta_eta
// q_hat = beta_2 * (M_sec * q_eta_eta + E)   where E has entries > q_max

export function doQueryStep2(qDot, secrets, maxNorm) {
  const { c, ep, eta, Mbase } = secrets;
  const qMax = vectorMax(qDot);

  // Build M_t: invertible, with diagonal/off-diagonal magnitude constraints.
  const maxNormInt = Math.ceil(maxNorm);
  const qMaxInt = Math.ceil(qMax);
  let Mt;
  for (let attempt = 0; attempt < 32; attempt++) {
    Mt = randUniformMatrix(eta, eta); // small base noise
    for (let i = 0; i < eta; i++) {
      for (let j = 0; j < eta; j++) {
        if (i === j) {
          Mt[i][j] = randInt(maxNormInt, maxNormInt + 100);
        } else {
          Mt[i][j] = randInt(qMaxInt, qMaxInt + 100);
        }
      }
    }
    if (Math.abs(det(Mt)) > 1e-9) break;
  }

  const Msec = toPlain(matMul(Mt, Mbase));

  const x = randIntVector(c, 0, 10);
  const qPrime = concat(qDot, [1], x, zeros(ep)); // length eta
  const qEtaEta = diag(qPrime);

  const product = toPlain(matMul(Msec, qEtaEta));

  // Error matrix E: entries > q_max so QU cannot peek at Msec.
  const E = randIntMatrix(eta, eta, qMaxInt, qMaxInt + 100);
  const sum = toPlain(add(product, E));

  const beta2 = Math.random() + 0.5; // any positive real
  const qHat = toPlain(scalarMul(beta2, sum));

  return { qHat, Mt, beta2 };
}

// ----- Query User: step 3 ----------------------------------------------------
// Build N' (eta x eta diag) with first d entries from N and rest = 1.
// q_tilde_enc = q_hat . N'^{-1}
// q_tilde_vec_j = sum_i q_tilde_enc[j][i]

export function quQueryStep3(qHat, Nvalues, eta) {
  const d = Nvalues.length;
  const NprimeValues = new Array(eta);
  for (let i = 0; i < eta; i++) {
    NprimeValues[i] = i < d ? Nvalues[i] : 1;
  }
  const NprimeInvValues = NprimeValues.map((v) => 1 / v);
  const NprimeInv = diag(NprimeInvValues);
  const qTildeEnc = toPlain(matMul(qHat, NprimeInv));
  const qTildeVec = rowSum(qTildeEnc);
  return { qTildeVec };
}
