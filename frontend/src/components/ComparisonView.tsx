import React, { useEffect, useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, Cell, CartesianGrid
} from 'recharts';
import { 
  Loader, CheckCircle2, XCircle, ShieldCheck, Sparkles, Clock, 
  Lock, Database, EyeOff
} from 'lucide-react';
import { api } from '../api';

interface ComparisonProps {
  sessionId: string;
}

interface SessionData {
  session_id: string;
  dataset_name: string;
  status: string;
  secure_duration: string | null;
  baseline_duration: string | null;
  artifacts: string[];
  secure_knn_indices: number[] | null;
  baseline_knn_indices: number[] | null;
  data_og: number[][] | null;
  query_og: number[] | null;
}

export const ComparisonView: React.FC<ComparisonProps> = ({ sessionId }) => {
  const [data, setData] = useState<SessionData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStatus = async () => {
      setLoading(true);
      try {
        const status = await api.getSessionStatus(sessionId);
        setData(status);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchStatus();
  }, [sessionId]);

  if (loading || !data) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '350px', gap: '1rem' }}>
        <Loader className="loading-spinner" style={{ width: '40px', height: '40px', borderTopColor: 'var(--accent-cyan)' }} />
        <p style={{ fontStyle: 'italic', color: 'var(--text-secondary)' }}>Decrypting analytical metrics...</p>
      </div>
    );
  }

  const secureIndices = data.secure_knn_indices ?? [];
  const baselineIndices = data.baseline_knn_indices ?? [];

  // Correctness: how many of the secure indices match the baseline
  const matchingIndices = secureIndices.filter(i => baselineIndices.includes(i));
  const totalK = Math.max(secureIndices.length, baselineIndices.length, 1);
  const accuracyPct = Math.round((matchingIndices.length / totalK) * 100);

  // Performance chart data (converting seconds to milliseconds)
  const perfData = [
    {
      name: 'Plaintext k-NN (CPU)',
      duration: parseFloat(data.baseline_duration || '0') * 1000,
    },
    {
      name: 'Secure k-NN (ASPE Matrix)',
      duration: parseFloat(data.secure_duration || '0') * 1000,
    },
  ];

  const PERF_COLORS = ['#34d399', '#38bdf8']; // Success Emerald and Cyan

  // Per-neighbor comparison data for the grouped bar chart
  const neighborComparisonData = Array.from({ length: totalK }, (_, i) => ({
    name: `Neighbor K=${i + 1}`,
    baseline: baselineIndices[i] ?? -1,
    secure: secureIndices[i] ?? -1,
    match: baselineIndices[i] === secureIndices[i],
  }));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2.25rem' }}>
      
      {/* Session Title Bar */}
      <div className="glass-panel" style={{ padding: '2rem 2.25rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
              <span className="badge" style={{ background: 'rgba(56, 189, 248, 0.1)', color: 'var(--accent-cyan)', border: '1px solid rgba(56, 189, 248, 0.15)' }}>
                Session Evaluator
              </span>
              <span className="badge warning">
                {data.status}
              </span>
            </div>
            <h2 style={{ margin: 0, fontSize: '1.75rem', fontWeight: 800 }}>Dataset: {data.dataset_name}</h2>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', fontSize: '0.85rem' }}>
            <span style={{ color: 'var(--text-secondary)' }}>Session ID</span>
            <code style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-purple)', fontSize: '0.85rem' }}>{sessionId}</code>
          </div>
        </div>
      </div>

      {/* Accuracy Hero Banner Card */}
      <div
        className="glass-panel"
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '2.5rem',
          flexWrap: 'wrap',
          background:
            accuracyPct === 100
              ? 'linear-gradient(135deg, rgba(52,211,153,0.08) 0%, rgba(52,211,153,0.02) 100%)'
              : 'linear-gradient(135deg, rgba(251,113,133,0.08) 0%, rgba(251,113,133,0.02) 100%)',
          borderColor: accuracyPct === 100 ? 'rgba(52,211,153,0.3)' : 'rgba(251,113,133,0.3)',
        }}
      >
        <div
          style={{
            width: '90px',
            height: '90px',
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1.9rem',
            fontWeight: 800,
            fontFamily: 'var(--font-headings)',
            background: accuracyPct === 100 ? 'rgba(52,211,153,0.15)' : 'rgba(251,113,133,0.15)',
            color: accuracyPct === 100 ? 'var(--success-color)' : 'var(--danger-color)',
            boxShadow: accuracyPct === 100 ? '0 0 25px rgba(52,211,153,0.15)' : '0 0 25px rgba(251,113,133,0.15)',
            border: `2px solid ${accuracyPct === 100 ? 'var(--success-color)' : 'var(--danger-color)'}`,
            flexShrink: 0,
          }}
        >
          {accuracyPct}%
        </div>
        <div style={{ flex: 1, minWidth: '280px' }}>
          <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '1.35rem', fontWeight: 700 }}>
            <ShieldCheck size={22} style={{ color: accuracyPct === 100 ? 'var(--success-color)' : 'var(--danger-color)' }} />
            Asymmetric Homomorphic Accuracy Score
          </h3>
          <p style={{ marginTop: '0.45rem', fontSize: '0.95rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
            Exactly <strong style={{ color: 'var(--text-primary)' }}>{matchingIndices.length}</strong> out of{' '}
            <strong style={{ color: 'var(--text-primary)' }}>{totalK}</strong> homomorphic k-nearest neighbors returned 
            by the cloud correspond fully with standard, plaintext Euclidean computations. The scalar product order is fully preserved.
          </p>
        </div>
      </div>

      {/* Analytics Charts Grid */}
      <div className="grid-2">
        {/* Performance Speed Timing */}
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column' }}>
          <h2 style={{ fontSize: '1.25rem', marginBottom: '0.25rem' }}>
            <Clock size={16} style={{ color: 'var(--accent-cyan)' }} />
            Evaluation Overhead (ms)
          </h2>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
            Homomorphic encryption runtime vs plaintext execution.
          </p>
          <div style={{ width: '100%', height: 260, marginTop: 'auto' }}>
            <ResponsiveContainer>
              <BarChart data={perfData} margin={{ top: 10, right: 10, left: -10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" vertical={false} />
                <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 11, fontWeight: 500 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                <Tooltip
                  cursor={{ fill: 'rgba(255,255,255,0.02)' }}
                  contentStyle={{
                    backgroundColor: 'rgba(15, 23, 42, 0.95)',
                    border: '1px solid var(--panel-border)',
                    borderRadius: '12px',
                    color: '#fff',
                    boxShadow: '0 10px 25px rgba(0, 0, 0, 0.3)',
                    fontFamily: 'var(--font-family)',
                  }}
                  formatter={(v: any) => [`${parseFloat(v || 0).toFixed(3)} ms`, 'Overhead']}
                />
                <Bar dataKey="duration" radius={[6, 6, 0, 0]} maxBarSize={60}>
                  {perfData.map((_, idx) => (
                    <Cell key={idx} fill={PERF_COLORS[idx]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Per-Neighbor Index Correlation */}
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column' }}>
          <h2 style={{ fontSize: '1.25rem', marginBottom: '0.25rem' }}>
            <Sparkles size={16} style={{ color: 'var(--accent-purple)' }} />
            Neighbor Coordinate Index Correlation
          </h2>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
            Indices returned by standard k-NN (green) vs ASPE k-NN (blue).
          </p>
          <div style={{ width: '100%', height: 260, marginTop: 'auto' }}>
            <ResponsiveContainer>
              <BarChart
                data={neighborComparisonData}
                margin={{ top: 10, right: 10, left: -10, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" vertical={false} />
                <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 11, fontWeight: 500 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                <Tooltip
                  cursor={{ fill: 'rgba(255,255,255,0.02)' }}
                  contentStyle={{
                    backgroundColor: 'rgba(15, 23, 42, 0.95)',
                    border: '1px solid var(--panel-border)',
                    borderRadius: '12px',
                    color: '#fff',
                    boxShadow: '0 10px 25px rgba(0, 0, 0, 0.3)',
                    fontFamily: 'var(--font-family)',
                  }}
                />
                <Legend iconType="circle" wrapperStyle={{ fontSize: 11, marginTop: 10 }} />
                <Bar dataKey="baseline" name="Plaintext Index" fill="var(--success-color)" radius={[4, 4, 0, 0]} maxBarSize={25} />
                <Bar dataKey="secure" name="Secure Index" fill="var(--accent-cyan)" radius={[4, 4, 0, 0]} maxBarSize={25} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Neighbor-by-Neighbor Match Detail Table */}
      <div className="glass-panel">
        <h2 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>
          <Sparkles size={16} style={{ color: 'var(--success-color)' }} />
          Exact Nearest Neighbors Correlation Table
        </h2>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
          Comparing coordinate rows returned at each K level to check ordering consistency.
        </p>
        
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Rank Order</th>
                <th>Plaintext Row Index</th>
                <th>Secure Homomorphic Row</th>
                <th>Vector Match Integrity</th>
              </tr>
            </thead>
            <tbody>
              {neighborComparisonData.map((row, i) => (
                <tr key={i}>
                  <td style={{ fontWeight: 600 }}>{i + 1}</td>
                  <td>
                    {row.baseline === -1 ? '—' : (
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.45rem' }}>
                        <Database size={14} style={{ color: 'var(--success-color)' }} /> Row #{row.baseline}
                      </span>
                    )}
                  </td>
                  <td>
                    {row.secure === -1 ? '—' : (
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.45rem' }}>
                        <Lock size={14} style={{ color: 'var(--accent-cyan)' }} /> Encrypted Row #{row.secure}
                      </span>
                    )}
                  </td>
                  <td>
                    {row.match ? (
                      <span className="badge" style={{ padding: '0.25rem 0.65rem' }}>
                        <CheckCircle2 size={13} /> Complete Integrity
                      </span>
                    ) : (
                      <span className="badge pending" style={{ padding: '0.25rem 0.65rem' }}>
                        <XCircle size={13} /> Discrepancy
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Cryptographic Artifact Trace */}
      <div className="glass-panel">
        <h2 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>
          <Lock size={16} style={{ color: 'var(--accent-cyan)' }} />
          Homomorphic Artifact &amp; Token Trace
        </h2>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
          Secure parameters generated and exchanged during homomorphic evaluation.
        </p>

        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Cryptographic Artifact Name</th>
                <th>Origin Actor Space</th>
                <th>Security / Visibility Level</th>
              </tr>
            </thead>
            <tbody>
              {data.artifacts?.map((art: string) => {
                let actor = 'System Service';
                let typeBadge = <span className="badge neutral"><EyeOff size={11} /> Intermediate Matrix</span>;
                
                if (art.includes('query_1') || art.includes('N') || art.includes('beta_1')) {
                  actor = 'Query User (Stage 1)';
                  typeBadge = <span className="badge warning"><Lock size={11} /> Client Secret Private Key</span>;
                }
                if (
                  art.includes('data_cloud') ||
                  art.includes('user_1') ||
                  art.includes('err') ||
                  art.includes('query_2')
                ) {
                  actor = 'Data Owner (ASPE)';
                  typeBadge = <span className="badge warning"><Lock size={11} /> Owner Matrix Key</span>;
                }
                if (art.includes('q_dash')) {
                  actor = 'Query User (Stage 2)';
                  typeBadge = <span className="badge"><Lock size={11} /> Transformed Query</span>;
                }
                if (art.includes('knnResult') || art.includes('baselineKnn')) {
                  actor = 'Cloud CSP Evaluator';
                  typeBadge = <span className="badge neutral"><Sparkles size={11} /> Result Indices</span>;
                }

                return (
                  <tr key={art}>
                    <td>
                      <code>{art}</code>
                    </td>
                    <td style={{ fontWeight: 500 }}>{actor}</td>
                    <td>{typeBadge}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
