import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { AnalysisItem, listAnalyses } from '../services/api';

export default function HistoryPage() {
  const navigate = useNavigate();
  const [analyses, setAnalyses] = useState<AnalysisItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadAnalyses() {
      try {
        const data = await listAnalyses();
        setAnalyses(data);
      } catch (error) {
        console.error('Falha ao carregar análises', error);
      } finally {
        setLoading(false);
      }
    }

    void loadAnalyses();
  }, []);

  if (loading) {
    return <div className="card">Carregando histórico...</div>;
  }

  return (
    <section className="card">
      <span className="eyebrow">Histórico</span>
      <h2>Minhas análises</h2>

      <div className="history-list">
        {analyses.length === 0 ? (
          <p>Nenhuma análise registrada ainda.</p>
        ) : (
          analyses.map((item) => (
            <button
              key={item.id}
              type="button"
              className="history-item"
              onClick={() => navigate('/analysis', { state: { analysisId: item.id } })}
            >
              <div>
                <strong>{item.title}</strong>
                <small>{new Date(item.created_at).toLocaleDateString('pt-BR')}</small>
              </div>
              <span className={`status status-${item.status.toLowerCase()}`}>{item.status}</span>
            </button>
          ))
        )}
      </div>
    </section>
  );
}
