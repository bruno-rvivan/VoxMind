import { useEffect, useState } from 'react';

import { AnalysisItem, getCurrentUser, listAnalyses } from '../services/api';

export default function DashboardPage() {
  const [userName, setUserName] = useState('Usuário');
  const [analyses, setAnalyses] = useState<AnalysisItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [user, data] = await Promise.all([getCurrentUser(), listAnalyses()]);
        setUserName(user.name);
        setAnalyses(data);
      } catch (error) {
        console.error('Falha ao carregar o dashboard', error);
      } finally {
        setLoading(false);
      }
    }

    void loadDashboard();
  }, []);

  const metrics = [
    { label: 'Análises', value: String(analyses.length), detail: 'registradas' },
    { label: 'Status', value: analyses.some((analysis) => analysis.status === 'completed') ? 'Ativo' : 'Em revisão', detail: 'monitoramento' },
    { label: 'Última análise', value: analyses[0]?.title ?? 'Sem dados', detail: analyses[0] ? 'recentemente' : 'ainda não' },
    { label: 'Clareza', value: analyses.length > 0 ? '87%' : '—', detail: 'média estimada' },
  ];

  if (loading) {
    return <div className="card">Carregando dashboard...</div>;
  }

  return (
    <section>
      <div className="section-heading">
        <div>
          <span className="eyebrow">Dashboard</span>
          <h2>Resumo da sua performance, {userName}</h2>
        </div>
      </div>

      <div className="metrics-grid">
        {metrics.map((metric) => (
          <div key={metric.label} className="card metric-card">
            <small>{metric.label}</small>
            <strong>{metric.value}</strong>
            <span>{metric.detail}</span>
          </div>
        ))}
      </div>

      <div className="card chart-card">
        <h3>Evolução ao longo do tempo</h3>
        <div className="bars" aria-label="Gráfico de evolução">
          <span style={{ height: '35%' }} />
          <span style={{ height: '48%' }} />
          <span style={{ height: '60%' }} />
          <span style={{ height: '56%' }} />
          <span style={{ height: '78%' }} />
          <span style={{ height: '82%' }} />
        </div>
      </div>
    </section>
  );
}
