import { FormEvent, useEffect, useMemo, useState } from 'react';
import { useLocation } from 'react-router-dom';

import {
  AnalysisReport,
  generateAnalysisReport,
  getAnalysisReport,
  listAnalyses,
  transcribeAndGenerateReport,
} from '../services/api';

type SegmentDraft = { start: string; end: string; text: string };
type AnalysisPageState = { analysisId?: string; autoTranscribe?: boolean };

export default function AnalysisPage() {
  const location = useLocation();
  const [report, setReport] = useState<AnalysisReport | null>(null);
  const [analysisId, setAnalysisId] = useState('');
  const [segments, setSegments] = useState<SegmentDraft[]>([
    { start: '0', end: '5', text: '' },
  ]);
  const [loading, setLoading] = useState(true);
  const [transcribing, setTranscribing] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const pageState = location.state as AnalysisPageState | null;

    async function loadReport() {
      try {
        setLoading(true);
        setError('');

        const stateAnalysisId = pageState?.analysisId;
        const fallbackAnalysisId = new URLSearchParams(location.search).get('analysisId');
        const analyses = await listAnalyses();
        const analysisId = stateAnalysisId ?? fallbackAnalysisId ?? analyses[0]?.id;

        if (!analysisId) {
          throw new Error('Nenhuma análise disponível para mostrar.');
        }

        setAnalysisId(analysisId);
        try {
          const nextReport = await getAnalysisReport(analysisId);
          setReport(nextReport);
        } catch (reportError) {
          if (
            reportError instanceof Error
            && reportError.message === 'Relatório ainda não gerado para esta análise.'
          ) {
            setReport(null);
            if (pageState?.autoTranscribe) {
              setTranscribing(true);
              try {
                setReport(await transcribeAndGenerateReport(analysisId));
              } finally {
                setTranscribing(false);
              }
            }
            return;
          }
          throw reportError;
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Não foi possível carregar o relatório.');
      } finally {
        setLoading(false);
      }
    }

    void loadReport();
  }, [location.search, location.state]);

  const handleTranscribe = async () => {
    if (!analysisId) return;
    setError('');
    setTranscribing(true);
    try {
      setReport(await transcribeAndGenerateReport(analysisId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Não foi possível transcrever o vídeo.');
    } finally {
      setTranscribing(false);
    }
  };

  const handleGenerateReport = async (event: FormEvent) => {
    event.preventDefault();
    setError('');

    const transcriptSegments = segments.map((segment) => ({
      start: Number(segment.start),
      end: Number(segment.end),
      text: segment.text.trim(),
    }));
    if (transcriptSegments.some((segment) => (
      !Number.isFinite(segment.start)
      || !Number.isFinite(segment.end)
      || segment.start < 0
      || segment.end <= segment.start
      || !segment.text
    ))) {
      setError('Confira os tempos e o texto de cada trecho. O fim deve ser maior que o início.');
      return;
    }

    setGenerating(true);
    try {
      const nextReport = await generateAnalysisReport(analysisId, {
        segments: transcriptSegments,
      });
      setReport(nextReport);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Não foi possível gerar o relatório.');
    } finally {
      setGenerating(false);
    }
  };

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
    return (
      <div className="card">
        {transcribing ? 'Transcrevendo o vídeo e gerando relatório...' : 'Carregando relatório...'}
      </div>
    );
  }

  if (error && !analysisId) {
    return <div className="card"><p className="form-error">{error}</p></div>;
  }

  if (!report) {
    return (
      <section className="card">
        <span className="eyebrow">Relatório</span>
        <h2>Gerar relatório da análise</h2>
        <p>
          O VoxMind pode transcrever o áudio do vídeo e calcular as métricas de fala. Na primeira
          execução, o modelo será baixado e o processamento poderá levar alguns minutos.
        </p>
        <button type="button" onClick={() => void handleTranscribe()} disabled={transcribing}>
          {transcribing ? 'Transcrevendo...' : 'Transcrever vídeo e gerar relatório'}
        </button>
        {error ? <p className="form-error">{error}</p> : null}

        <details className="manual-transcript">
          <summary>Inserir transcrição manualmente</summary>
          <form className="stacked-form" onSubmit={handleGenerateReport}>
            {segments.map((segment, index) => (
              <div className="transcript-segment" key={index}>
                <div className="results-grid">
                  <label>
                    Início (s)
                    <input
                      type="number"
                      min="0"
                      step="0.1"
                      required
                      value={segment.start}
                      onChange={(event) => setSegments((current) => current.map((item, itemIndex) => (
                        itemIndex === index ? { ...item, start: event.target.value } : item
                      )))}
                    />
                  </label>
                  <label>
                    Fim (s)
                    <input
                      type="number"
                      min="0.1"
                      step="0.1"
                      required
                      value={segment.end}
                      onChange={(event) => setSegments((current) => current.map((item, itemIndex) => (
                        itemIndex === index ? { ...item, end: event.target.value } : item
                      )))}
                    />
                  </label>
                  <label>
                    Trecho transcrito
                    <input
                      type="text"
                      required
                      value={segment.text}
                      onChange={(event) => setSegments((current) => current.map((item, itemIndex) => (
                        itemIndex === index ? { ...item, text: event.target.value } : item
                      )))}
                      placeholder="Digite o que foi falado neste intervalo"
                    />
                  </label>
                </div>
                {segments.length > 1 ? (
                  <button
                    type="button"
                    className="secondary"
                    onClick={() => setSegments((current) => current.filter((_, itemIndex) => itemIndex !== index))}
                    aria-label={`Remover trecho ${index + 1}`}
                  >
                    Remover trecho
                  </button>
                ) : null}
              </div>
            ))}
            <div className="cta-row">
              <button
                type="button"
                className="secondary"
                onClick={() => setSegments((current) => [
                  ...current,
                  { start: '', end: '', text: '' },
                ])}
              >
                Adicionar trecho
              </button>
              <button type="submit" disabled={generating}>
                {generating ? 'Gerando relatório...' : 'Gerar relatório manual'}
              </button>
            </div>
            {error ? <p className="form-error">{error}</p> : null}
          </form>
        </details>
      </section>
    );
  }

  return (
    <section>
      <div className="section-heading">
        <div>
          <span className="eyebrow">Relatório</span>
          <h2>{report.summary}</h2>
        </div>
      </div>

      <button type="button" className="secondary" onClick={() => void handleTranscribe()} disabled={transcribing}>
        {transcribing ? 'Transcrevendo...' : 'Refazer transcrição a partir do vídeo'}
      </button>
      {error ? <p className="form-error">{error}</p> : null}

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
