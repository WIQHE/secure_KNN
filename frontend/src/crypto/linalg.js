// Thin wrappers around math.js. All helpers return plain nested JS arrays
// so callers can pass them straight to JSON.stringify.

import * as math from 'mathjs';

const M = () => math;

export function randInt(lo, hi) {
  // Inclusive lo, exclusive hi.
  return Math.floor(Math.random() * (hi - lo)) + lo;
}

export function randIntMatrix(rows, cols, lo, hi) {
  const out = [];
  for (let i = 0; i < rows; i++) {
    const row = new Array(cols);
    for (let j = 0; j < cols; j++) row[j] = randInt(lo, hi);
    out.push(row);
  }
  return out;
}

export function randIntVector(n, lo, hi) {
  const out = new Array(n);
  for (let i = 0; i < n; i++) out[i] = randInt(lo, hi);
  return out;
}

export function randUniformMatrix(rows, cols) {
  const out = [];
  for (let i = 0; i < rows; i++) {
    const row = new Array(cols);
    for (let j = 0; j < cols; j++) row[j] = Math.random();
    out.push(row);
  }
  return out;
}

export function zeros(n) {
  return new Array(n).fill(0);
}

export function diag(values) {
  const n = values.length;
  const out = [];
  for (let i = 0; i < n; i++) {
    const row = new Array(n).fill(0);
    row[i] = values[i];
    out.push(row);
  }
  return out;
}

export function setDiagonal(matrix, values) {
  for (let i = 0; i < values.length; i++) matrix[i][i] = values[i];
  return matrix;
}

export function matMul(a, b) {
  return M().multiply(a, b);
}

export function matInv(a) {
  return M().inv(a);
}

export function det(a) {
  return M().det(a);
}

export function transpose(a) {
  return M().transpose(a);
}

export function add(a, b) {
  return M().add(a, b);
}

export function scalarMul(s, a) {
  return M().multiply(s, a);
}

export function rowSum(matrix) {
  // Returns a length-rows vector whose j-th entry is sum_i matrix[j][i].
  return matrix.map((row) => row.reduce((acc, v) => acc + v, 0));
}

export function vectorMax(vec) {
  let m = -Infinity;
  for (const v of vec) if (v > m) m = v;
  return m;
}

export function vectorNorm(vec) {
  let s = 0;
  for (const v of vec) s += v * v;
  return Math.sqrt(s);
}

export function vectorNormSquared(vec) {
  let s = 0;
  for (const v of vec) s += v * v;
  return s;
}

export function maxRowNorm(matrix) {
  let m = 0;
  for (const row of matrix) {
    const n = vectorNorm(row);
    if (n > m) m = n;
  }
  return m;
}

export function concat(...arrays) {
  return [].concat(...arrays);
}

export function toPlain(value) {
  // math.js may return a DenseMatrix; normalize to nested JS arrays.
  if (value && typeof value.toArray === 'function') return value.toArray();
  return value;
}
