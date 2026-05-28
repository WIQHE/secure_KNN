const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface SessionInfo {
  id: string;
  status: string;
  dataset_name: string;
  created_at: string;
  secure_duration: string | null;
  baseline_duration: string | null;
}

export const api = {
  getSessions: async (): Promise<SessionInfo[]> => {
    const res = await fetch(`${API_URL}/sessions`);
    return res.json();
  },
  
  createSession: async (datasetName: string = 'Smoke Test'): Promise<{session_id: string, status: string}> => {
    const formData = new FormData();
    formData.append('dataset_name', datasetName);
    const res = await fetch(`${API_URL}/sessions`, {
      method: 'POST',
      body: formData
    });
    return res.json();
  },

  uploadDataset: async (sessionId: string, file: File): Promise<any> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_URL}/sessions/${sessionId}/upload`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  runBaselineKnn: async (sessionId: string, k: number = 3): Promise<any> => {
    const res = await fetch(`${API_URL}/sessions/${sessionId}/baseline_knn`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ k, return_data: true })
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  runSecurePipeline: async (sessionId: string, params: any = {}): Promise<any> => {
    const res = await fetch(`${API_URL}/sessions/${sessionId}/pipeline/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ params })
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  runPipelineStep: async (sessionId: string, stepName: string, params: any = {}): Promise<any> => {
    const res = await fetch(`${API_URL}/sessions/${sessionId}/pipeline/step/${stepName}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  getSessionStatus: async (sessionId: string): Promise<any> => {
    const res = await fetch(`${API_URL}/sessions/${sessionId}/status`);
    return res.json();
  }
};
