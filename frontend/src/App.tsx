import { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { Dashboard } from './components/Dashboard';
import { ComparisonView } from './components/ComparisonView';
import { ArrowLeft } from 'lucide-react';

function App() {
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);

  return (
    <div className="app-container">
      <Sidebar 
        currentSessionId={currentSessionId} 
        onSelectSession={(id) => setCurrentSessionId(id)} 
      />
      
      <main className="main-content">
        {currentSessionId ? (
          <div>
            <button 
              className="btn-secondary" 
              style={{ marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 1rem', borderRadius: '8px' }}
              onClick={() => setCurrentSessionId(null)}
            >
              <ArrowLeft size={16} /> New Run
            </button>
            <ComparisonView sessionId={currentSessionId} />
          </div>
        ) : (
          <Dashboard onSessionStarted={(id) => setCurrentSessionId(id)} />
        )}
      </main>
    </div>
  );
}

export default App;
