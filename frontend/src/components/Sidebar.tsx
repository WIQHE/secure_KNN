import React, { useEffect, useState } from 'react';
import { Database, Clock, RefreshCw, ShieldAlert, Sparkles } from 'lucide-react';
import { api, SessionInfo } from '../api';

interface SidebarProps {
  currentSessionId: string | null;
  onSelectSession: (id: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentSessionId, onSelectSession }) => {
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchSessions = async () => {
    setLoading(true);
    try {
      const data = await api.getSessions();
      setSessions(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, [currentSessionId]);

  return (
    <div className="sidebar">
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
          <h2 style={{ margin: 0, fontSize: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.65rem', fontWeight: 800, letterSpacing: '-0.02em' }}>
            <Database size={20} className="text-cyan" style={{ color: 'var(--accent-cyan)' }} />
            Console History
          </h2>
          <button 
            className="btn-secondary" 
            style={{ padding: '0.5rem', borderRadius: '8px', border: '1px solid var(--panel-border)', cursor: 'pointer', display: 'flex', alignItems: 'center' }} 
            onClick={fetchSessions}
            disabled={loading}
            title="Refresh Runs"
          >
            <RefreshCw size={14} className={loading ? 'spin-slow' : ''} />
          </button>
        </div>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Track and analyze secure homomorphic pipeline computations.</p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', overflowY: 'auto', flex: 1, paddingRight: '0.25rem' }}>
        {loading && sessions.length === 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)', padding: '1rem', fontStyle: 'italic' }}>
            <RefreshCw size={14} className="spin-slow" /> Loading history...
          </div>
        )}
        {!loading && sessions.length === 0 && (
          <div style={{ padding: '2rem 1rem', textAlign: 'center', border: '1px dashed var(--panel-border)', borderRadius: '12px', background: 'rgba(255,255,255,0.01)' }}>
            <ShieldAlert size={24} style={{ color: 'var(--text-secondary)', marginBottom: '0.5rem', opacity: 0.5 }} />
            <p style={{ fontSize: '0.85rem' }}>No previous execution runs.</p>
          </div>
        )}
        {sessions.map(s => {
          const isSelected = currentSessionId === s.id;
          const isCompleted = s.status === 'completed';
          const isFailed = s.status?.startsWith('failed');

          return (
            <div 
              key={s.id} 
              className={`session-item ${isSelected ? 'active' : ''}`}
              onClick={() => onSelectSession(s.id)}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.5rem' }}>
                <h3 style={{ margin: 0, textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                  {s.dataset_name}
                </h3>
                {isCompleted && <Sparkles size={14} style={{ color: 'var(--accent-cyan)', flexShrink: 0 }} />}
              </div>
              
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', marginTop: '0.45rem', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                <Clock size={12} />
                <span>{new Date(s.created_at).toLocaleDateString()} {new Date(s.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
              </div>
              
              <div style={{ marginTop: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span className={`badge ${isCompleted ? '' : isFailed ? 'pending' : 'warning'}`}>
                  {s.status}
                </span>
                {s.secure_duration && (
                  <span style={{ fontSize: '0.75rem', color: 'var(--accent-purple)' }}>
                    {parseFloat(s.secure_duration).toFixed(2)}s
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
