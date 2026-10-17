import { useEffect, useMemo, useState } from 'react';
import { useLocation } from 'react-router-dom';

import { AnalysisReport, getAnalysisReport, listAnalyses } from '../services/api';

export default function AnalysisPage() {
  const location = useLocation();
  const [report, setReport] = useState<AnalysisReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function loadReport() {
      try {
        setLoading(true);
        setError('');

        const stateAnalysisId = (location.state as { analysisId?: string } | null)?.analysisId;
        const fallbackAnalysisId = new URLSearchParams(location.search).get('analysisId');
        const analyses = await listAnalyses();
        const analysisId = stateAnalysisId ?? fallbackAnalysisId ?? analyses[0]?.id;

        if (!analysisId) {
          throw new Error('Nenhuma análise disponível para mostrar.');
        }

        const nextReport = await getAnalysisReport(analysisId);
        setReport(nextReport);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Não foi possível carregar o relatório.');
      } finally {
        setLoading(false);
      }
    }

    void loadReport();
  }, [location.search, location.state]);

  const metrics = useMemo(() => {
    if (!report) return [];

    return [
      { label: 'Score geral', value: `${report.overall_score.toFixed(1)} / 100` },
      { label: 'Pausas', value: String(report.metrics.pause_count ?? 0) },
      { label: 'Palavras por minuto', value: String(report.metrics.words_per_minute ?? 0) },
      { label: 'Repetições', value: String(report.metrics.adjacent_repetition_count ?? 0) },
    ];
  }, [report]);

  if (loading) {
    return <div className="card">Carregando relatório...</div>;
  }

  if (error) {
    return <div className="card"><p className="form-error">{error}</p></div>;
  }

  if (!report) {
    return <div className="card">Nenhum relatório disponível.</div>;
  }

  return (
    <section>
      <div className="section-heading">
        <div>
          <span className="eyebrow">Relatório</span>
          <h2>{report.summary}</h2>
        </div>
      </div>

      <div className="metrics-grid">
        {metrics.map((metric) => (
          <div key={metric.label} className="card metric-card compact">
            <small>{metric.label}</small>
            <strong>{metric.value}</strong>
          </div>
        ))}
      </div>

      <div className="results-grid">
        <article className="card">
          <h3>Resumo</h3>
          <p>{report.summary}</p>
        </article>

        <article className="card">
          <h3>Highlights</h3>
          <ul>
            {report.highlights.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>
      </div>
    </section>
  );
}
