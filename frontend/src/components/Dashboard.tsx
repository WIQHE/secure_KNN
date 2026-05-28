import React, { useRef, useState } from 'react';
import { 
  Upload, Play, Loader, ShieldCheck, Database, Cpu, Layers, 
  Settings, CheckCircle2, AlertCircle, ArrowRight
} from 'lucide-react';
import { api } from '../api';

interface DashboardProps {
  onSessionStarted: (sessionId: string) => void;
}

interface StepProgress {
  id: string;
  name: string;
  actor: 'Query User' | 'Data Owner' | 'Cloud Server' | 'System';
  description: string;
  status: 'idle' | 'running' | 'completed' | 'failed';
}

export const Dashboard: React.FC<DashboardProps> = ({ onSessionStarted }) => {
  const [loading, setLoading] = useState(false);
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(-1);
  const [error, setError] = useState('');
  
  // Custom pipeline parameters
  const [nRows, setNRows] = useState(15);
  const [dDims, setDDims] = useState(5);
  const [cNoise, setCNoise] = useState(3);
  const [epNoise, setEpNoise] = useState(2);
  const [kNeighbors, setKNeighbors] = useState(3);
  
  const [showConfig, setShowConfig] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Exquisite pipeline steps definitions
  const [steps, setSteps] = useState<StepProgress[]>([
    { id: 'session', name: 'Initialize Session', actor: 'System', description: 'Establishing secure session & cryptographic keys space', status: 'idle' },
    { id: 'generate_data', name: 'Data Generation', actor: 'System', description: 'Generating synthetic multi-dimensional original dataset', status: 'idle' },
    { id: 'generate_query', name: 'Query Generation', actor: 'Query User', description: 'Generating plaintext query vector to search coordinates', status: 'idle' },
    { id: 'query_stage1', name: 'Query Encryption (Stage 1)', actor: 'Query User', description: 'Multiplying query by secret matrix N & random scalar beta_1', status: 'idle' },
    { id: 'data_owner', name: 'Data Owner Encryption', actor: 'Data Owner', description: 'Encrypting full dataset using ASPE & double-encrypting Query Stage 1', status: 'idle' },
    { id: 'query_stage2', name: 'Query Finalization (Stage 2)', actor: 'Query User', description: 'Removing secret matrix N to isolate transformed query for cloud', status: 'idle' },
    { id: 'cloud_knn', name: 'Cloud-Side Homomorphic k-NN', actor: 'Cloud Server', description: 'Applying m_temp, computing distances without decryption, sorting top-K', status: 'idle' },
    { id: 'baseline', name: 'Euclidean Verification', actor: 'System', description: 'Computing standard Euclidean k-NN in plaintext to verify correctness', status: 'idle' }
  ]);

  const updateStepStatus = (id: string, status: StepProgress['status']) => {
    setSteps(prev => prev.map(s => s.id === id ? { ...s, status } : s));
  };

  const resetSteps = () => {
    setSteps(prev => prev.map(s => ({ ...s, status: 'idle' })));
    setCurrentStepIndex(-1);
  };

  const runSequentialSmokeTest = async () => {
    setLoading(true);
    setError('');
    resetSteps();
    
    let sessionId = '';
    try {
      // Step 0: Create Session
      setCurrentStepIndex(0);
      updateStepStatus('session', 'running');
      const sessionResult = await api.createSession(`Smoke Test (N=${nRows}, D=${dDims})`);
      sessionId = sessionResult.session_id;
      updateStepStatus('session', 'completed');
      
      // Step 1: Generate Data
      setCurrentStepIndex(1);
      updateStepStatus('generate_data', 'running');
      await api.runPipelineStep(sessionId, 'generate_data', { n: nRows, d: dDims, c: cNoise, ep: epNoise });
      updateStepStatus('generate_data', 'completed');

      // Step 2: Generate Query
      setCurrentStepIndex(2);
      updateStepStatus('generate_query', 'running');
      await api.runPipelineStep(sessionId, 'generate_query', { d: dDims });
      updateStepStatus('generate_query', 'completed');

      // Step 3: Query Stage 1
      setCurrentStepIndex(3);
      updateStepStatus('query_stage1', 'running');
      await api.runPipelineStep(sessionId, 'query_stage1');
      updateStepStatus('query_stage1', 'completed');

      // Step 4: Data Owner Process
      setCurrentStepIndex(4);
      updateStepStatus('data_owner', 'running');
      await api.runPipelineStep(sessionId, 'data_owner', { c: cNoise, ep: epNoise });
      updateStepStatus('data_owner', 'completed');

      // Step 5: Query Stage 2
      setCurrentStepIndex(5);
      updateStepStatus('query_stage2', 'running');
      await api.runPipelineStep(sessionId, 'query_stage2');
      updateStepStatus('query_stage2', 'completed');

      // Step 6: Cloud k-NN
      setCurrentStepIndex(6);
      updateStepStatus('cloud_knn', 'running');
      await api.runPipelineStep(sessionId, 'cloud_knn', { k: kNeighbors });
      updateStepStatus('cloud_knn', 'completed');

      // Step 7: Baseline Plaintext Comparison
      setCurrentStepIndex(7);
      updateStepStatus('baseline', 'running');
      await api.runBaselineKnn(sessionId, kNeighbors);
      updateStepStatus('baseline', 'completed');
      
      setTimeout(() => {
        onSessionStarted(sessionId);
      }, 600);
    } catch (err: any) {
      setError(err.message || 'An error occurred during step execution');
      const activeStepId = steps[currentStepIndex]?.id;
      if (activeStepId) {
        updateStepStatus(activeStepId, 'failed');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setError('');
    resetSteps();
    
    let sessionId = '';
    try {
      // Step 0: Create Session
      setCurrentStepIndex(0);
      updateStepStatus('session', 'running');
      const sessionResult = await api.createSession(file.name);
      sessionId = sessionResult.session_id;
      updateStepStatus('session', 'completed');
      
      // Step 1: Upload dataset
      setCurrentStepIndex(1);
      updateStepStatus('generate_data', 'running');
      const uploadRes = await api.uploadDataset(sessionId, file);
      const dimensions = uploadRes.shape[1] || dDims;
      setDDims(dimensions);
      updateStepStatus('generate_data', 'completed');

      // Step 2: Generate Query
      setCurrentStepIndex(2);
      updateStepStatus('generate_query', 'running');
      await api.runPipelineStep(sessionId, 'generate_query', { d: dimensions });
      updateStepStatus('generate_query', 'completed');

      // Step 3: Query Stage 1
      setCurrentStepIndex(3);
      updateStepStatus('query_stage1', 'running');
      await api.runPipelineStep(sessionId, 'query_stage1');
      updateStepStatus('query_stage1', 'completed');

      // Step 4: Data Owner Process
      setCurrentStepIndex(4);
      updateStepStatus('data_owner', 'running');
      await api.runPipelineStep(sessionId, 'data_owner', { c: cNoise, ep: epNoise });
      updateStepStatus('data_owner', 'completed');

      // Step 5: Query Stage 2
      setCurrentStepIndex(5);
      updateStepStatus('query_stage2', 'running');
      await api.runPipelineStep(sessionId, 'query_stage2');
      updateStepStatus('query_stage2', 'completed');

      // Step 6: Cloud k-NN
      setCurrentStepIndex(6);
      updateStepStatus('cloud_knn', 'running');
      await api.runPipelineStep(sessionId, 'cloud_knn', { k: kNeighbors });
      updateStepStatus('cloud_knn', 'completed');

      // Step 7: Baseline Plaintext Comparison
      setCurrentStepIndex(7);
      updateStepStatus('baseline', 'running');
      await api.runBaselineKnn(sessionId, kNeighbors);
      updateStepStatus('baseline', 'completed');
      
      setTimeout(() => {
        onSessionStarted(sessionId);
      }, 600);
    } catch (err: any) {
      setError(err.message || 'An error occurred processing the file upload');
      const activeStepId = steps[currentStepIndex]?.id;
      if (activeStepId) {
        updateStepStatus(activeStepId, 'failed');
      }
    } finally {
      setLoading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2.5rem' }}>
      {/* Dynamic Glassmorphic Hero Panel */}
      <div className="glass-panel" style={{ padding: '3rem', position: 'relative' }}>
        <div style={{ maxWidth: '850px', zIndex: 2, position: 'relative' }}>
          <span className="badge warning" style={{ marginBottom: '1.25rem' }}>
            <ShieldCheck size={14} /> Homomorphic Encryption Framework
          </span>
          <h1 style={{ marginBottom: '1rem', lineHeight: 1.15 }}>Secure k-NN Computation Console</h1>
          <p style={{ fontSize: '1.1rem', color: 'var(--text-secondary)', maxWidth: '700px', marginBottom: '1.5rem' }}>
            Outsource multi-dimensional datasets securely to untrusted Cloud Service Providers (CSPs). 
            Perform Asymmetric Scalar-Product-Preserving Encryption (ASPE) to compute exact k-Nearest Neighbors 
            without ever exposing plaintext data or user query coordinates.
          </p>
          <div style={{ display: 'flex', gap: '1rem' }}>
            <button className="btn" onClick={() => setShowConfig(!showConfig)} disabled={loading}>
              <Settings size={18} />
              {showConfig ? 'Hide Config' : 'Configure Parameters'}
            </button>
          </div>
        </div>

        {/* Glowing Decorative Element */}
        <div style={{
          position: 'absolute',
          right: '5%',
          top: '50%',
          transform: 'translateY(-50%)',
          width: '180px',
          height: '180px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(56,189,248,0.15) 0%, rgba(192,132,252,0.05) 50%, rgba(0,0,0,0) 100%)',
          filter: 'blur(10px)',
          pointerEvents: 'none'
        }} />
      </div>

      {/* Parameter Configuration Sub-panel */}
      {showConfig && (
        <div className="glass-panel" style={{ animation: 'pulseGlow 1s ease-in-out' }}>
          <h2 style={{ fontSize: '1.3rem', marginBottom: '1.5rem', borderBottom: '1px solid var(--panel-border)', paddingBottom: '0.75rem' }}>
            <Settings size={18} style={{ color: 'var(--accent-cyan)' }} />
            Cryptographic Configuration & Params
          </h2>
          <div className="grid-2" style={{ gap: '2rem' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div>
                <label style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.9rem', fontWeight: 600 }}>
                  <span>Dataset Rows (N)</span>
                  <span style={{ color: 'var(--accent-cyan)' }}>{nRows}</span>
                </label>
                <input 
                  type="range" min="10" max="100" step="5" value={nRows} 
                  onChange={(e) => setNRows(Number(e.target.value))}
                  style={{ width: '100%', accentColor: 'var(--accent-cyan)' }} 
                  disabled={loading}
                />
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Size of synthetic dataset generated</span>
              </div>
              
              <div>
                <label style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.9rem', fontWeight: 600 }}>
                  <span>Vector Dimensions (D)</span>
                  <span style={{ color: 'var(--accent-cyan)' }}>{dDims}</span>
                </label>
                <input 
                  type="range" min="3" max="25" step="1" value={dDims} 
                  onChange={(e) => setDDims(Number(e.target.value))}
                  style={{ width: '100%', accentColor: 'var(--accent-cyan)' }}
                  disabled={loading}
                />
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Dimensions per coordinate point</span>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', fontWeight: 600 }}>
                    c (Artificial variables)
                  </label>
                  <input 
                    type="number" min="1" max="10" value={cNoise} 
                    onChange={(e) => setCNoise(Number(e.target.value))}
                    style={{ width: '100%', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--panel-border)', padding: '0.5rem', borderRadius: '8px', color: 'white' }}
                    disabled={loading}
                  />
                </div>
                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', fontWeight: 600 }}>
                    ep (Error dimensions)
                  </label>
                  <input 
                    type="number" min="1" max="10" value={epNoise} 
                    onChange={(e) => setEpNoise(Number(e.target.value))}
                    style={{ width: '100%', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--panel-border)', padding: '0.5rem', borderRadius: '8px', color: 'white' }}
                    disabled={loading}
                  />
                </div>
              </div>
              
              <div>
                <label style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.9rem', fontWeight: 600 }}>
                  <span>Nearest Neighbors (K)</span>
                  <span style={{ color: 'var(--accent-purple)' }}>{kNeighbors}</span>
                </label>
                <input 
                  type="range" min="1" max="10" step="1" value={kNeighbors} 
                  onChange={(e) => setKNeighbors(Number(e.target.value))}
                  style={{ width: '100%', accentColor: 'var(--accent-purple)' }}
                  disabled={loading}
                />
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Number of nearest neighbors to query (top K)</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Execution Actions Grid */}
      <div className="grid-2">
        {/* Synthetic Smoke Test Card */}
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', minHeight: '340px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.25rem' }}>
              <div style={{ background: 'rgba(192, 132, 252, 0.1)', padding: '0.65rem', borderRadius: '12px' }}>
                <Cpu size={24} style={{ color: 'var(--accent-purple)' }} />
              </div>
              <h2 style={{ margin: 0, fontSize: '1.4rem' }}>Generate &amp; Run Pipeline</h2>
            </div>
            <p style={{ marginBottom: '1.5rem' }}>
              Execute the full homomorphic pipeline with synthetic datasets. Excellent for understanding 
              each mathematical boundary step-by-step and verifying accuracy immediately.
            </p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '1.5rem' }}>
              <span className="badge neutral">N = {nRows} Rows</span>
              <span className="badge neutral">D = {dDims} Dimensions</span>
              <span className="badge neutral">c = {cNoise} Noise</span>
              <span className="badge neutral">K = {kNeighbors} Neighbors</span>
            </div>
          </div>

          <button 
            className="btn" 
            style={{ width: '100%', height: '52px' }} 
            onClick={runSequentialSmokeTest} 
            disabled={loading}
          >
            {loading ? <Loader className="loading-spinner" /> : <Play size={20} />}
            {loading ? 'Executing Crypto Handshakes...' : 'Launch k-NN Pipeline'}
          </button>
        </div>

        {/* Custom Dataset Upload Card */}
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', minHeight: '340px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.25rem' }}>
              <div style={{ background: 'rgba(56, 189, 248, 0.1)', padding: '0.65rem', borderRadius: '12px' }}>
                <Database size={24} style={{ color: 'var(--accent-cyan)' }} />
              </div>
              <h2 style={{ margin: 0, fontSize: '1.4rem' }}>Upload Custom Dataset</h2>
            </div>
            <p style={{ marginBottom: '1.5rem' }}>
              Upload your own multi-dimensional numeric data as a CSV file. The console will automatically 
              encrypt and evaluate k-NN queries against it securely on the remote server.
            </p>
          </div>

          <label className="file-upload-label" style={{ padding: '2.5rem 1.5rem' }}>
            <Upload size={32} style={{ color: 'var(--accent-cyan)', marginBottom: '0.75rem' }} />
            <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Click to browse CSV dataset</span>
            <span style={{ fontSize: '0.75rem', marginTop: '0.25rem' }}>Rows will be encrypted instantly</span>
            <input 
              type="file" 
              accept=".csv" 
              ref={fileInputRef}
              onChange={handleFileUpload} 
              disabled={loading}
            />
          </label>
        </div>
      </div>

      {/* Sequential Execution Live Timeline Flow */}
      {(loading || currentStepIndex >= 0) && (
        <div className="glass-panel" style={{ borderLeft: '4px solid var(--accent-cyan)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem', borderBottom: '1px solid var(--panel-border)', paddingBottom: '1rem' }}>
            <h2 style={{ margin: 0, fontSize: '1.3rem' }}>
              <Layers size={18} style={{ color: 'var(--accent-cyan)' }} />
              Homomorphic Execution Handshake Timeline
            </h2>
            {loading ? (
              <span className="badge warning animate-pulse">
                <Loader size={12} className="spin-slow" /> Running Stage {currentStepIndex + 1}/8
              </span>
            ) : error ? (
              <span className="badge pending">
                <AlertCircle size={12} /> Execution Aborted
              </span>
            ) : (
              <span className="badge">
                <ShieldCheck size={12} /> Handshake Complete
              </span>
            )}
          </div>

          {error && (
            <div className="badge pending" style={{ width: '100%', marginBottom: '1.5rem', padding: '1rem', borderRadius: '12px', justifyContent: 'flex-start', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <AlertCircle size={18} style={{ color: 'var(--danger-color)' }} />
              <span style={{ fontSize: '0.9rem', fontWeight: 500 }}>{error}</span>
            </div>
          )}

          <div className="timeline-stepper">
            {steps.map((step, idx) => {
              const isRunning = step.status === 'running';
              const isCompleted = step.status === 'completed';
              const isFailed = step.status === 'failed';

              return (
                <div 
                  key={step.id} 
                  className={`timeline-step ${isRunning ? 'active' : ''} ${isCompleted ? 'completed' : ''}`}
                >
                  <div className="timeline-node">
                    {isCompleted ? (
                      <CheckCircle2 size={16} style={{ color: 'var(--success-color)' }} />
                    ) : isRunning ? (
                      <Loader size={16} className="spin-slow" style={{ color: 'var(--accent-cyan)' }} />
                    ) : isFailed ? (
                      <AlertCircle size={16} style={{ color: 'var(--danger-color)' }} />
                    ) : (
                      idx + 1
                    )}
                  </div>
                  
                  <div className="timeline-content">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <h4>{step.name}</h4>
                      <span className="badge neutral" style={{ fontSize: '0.7rem', padding: '0.15rem 0.45rem' }}>
                        {step.actor}
                      </span>
                    </div>
                    <p style={{ marginTop: '0.15rem' }}>{step.description}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Homomorphic Scheme Educational Architecture Flow */}
      {!loading && currentStepIndex === -1 && (
        <div className="glass-panel">
          <h2 style={{ fontSize: '1.3rem', marginBottom: '1.5rem' }}>
            <ShieldCheck size={18} style={{ color: 'var(--success-color)' }} />
            Cryptographic Flow Blueprint (ASPE Scheme)
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', position: 'relative' }}>
            
            {/* Step 1 Actor Card */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', background: 'rgba(255,255,255,0.01)', border: '1px solid var(--panel-border)', borderRadius: '12px', padding: '1.25rem' }}>
              <div style={{ background: 'rgba(192, 132, 252, 0.1)', padding: '0.5rem', borderRadius: '8px', color: 'var(--accent-purple)', fontWeight: 'bold', fontSize: '0.85rem' }}>
                Actor 1
              </div>
              <div style={{ flex: 1 }}>
                <h4 style={{ fontSize: '0.95rem', fontWeight: 700 }}>Query User (Alice)</h4>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  Constructs the query point, encrypts using its private key matrix N, and forwards the randomized query to the Data Owner.
                </p>
              </div>
              <ArrowRight size={18} style={{ color: 'var(--text-secondary)', opacity: 0.5 }} />
            </div>

            {/* Step 2 Actor Card */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', background: 'rgba(255, 255, 255, 0.01)', border: '1px solid var(--panel-border)', borderRadius: '12px', padding: '1.25rem' }}>
              <div style={{ background: 'rgba(56, 189, 248, 0.1)', padding: '0.5rem', borderRadius: '8px', color: 'var(--accent-cyan)', fontWeight: 'bold', fontSize: '0.85rem' }}>
                Actor 2
              </div>
              <div style={{ flex: 1 }}>
                <h4 style={{ fontSize: '0.95rem', fontWeight: 700 }}>Data Owner (Bob)</h4>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  Holds the dataset. Encrypts vectors into matrices using private matrix dimensions + artificial noise vectors, double-encrypts Alice's query and returns it.
                </p>
              </div>
              <ArrowRight size={18} style={{ color: 'var(--text-secondary)', opacity: 0.5 }} />
            </div>

            {/* Step 3 Actor Card */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', background: 'rgba(255, 255, 255, 0.01)', border: '1px solid var(--panel-border)', borderRadius: '12px', padding: '1.25rem' }}>
              <div style={{ background: 'rgba(52, 211, 153, 0.1)', padding: '0.5rem', borderRadius: '8px', color: 'var(--success-color)', fontWeight: 'bold', fontSize: '0.85rem' }}>
                Actor 3
              </div>
              <div style={{ flex: 1 }}>
                <h4 style={{ fontSize: '0.95rem', fontWeight: 700 }}>Cloud Server (CSP)</h4>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  Receives the encrypted dataset and final transformed encrypted query. Computes transformed absolute dot products (distances) and sorts indices homomorphically.
                </p>
              </div>
              <CheckCircle2 size={18} style={{ color: 'var(--success-color)' }} />
            </div>

          </div>
        </div>
      )}
    </div>
  );
};
