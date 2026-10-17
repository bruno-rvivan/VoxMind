import { FormEvent, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { uploadAnalysis } from '../services/api';

export default function UploadPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    title: '',
    language: 'pt',
    analysis_goal: '',
  });
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (!selectedFile) {
        throw new Error('Selecione um vídeo para enviar.');
      }

      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('title', form.title);
      formData.append('language', form.language);
      formData.append('analysis_goal', form.analysis_goal);

      await uploadAnalysis(formData);
      navigate('/history');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao criar a análise.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="card upload-panel">
      <span className="eyebrow">Nova análise</span>
      <h2>Enviar vídeo para processamento</h2>

      <div className="upload-box">
        <input
          type="file"
          accept="video/*"
          onChange={(event) => {
            const file = event.target.files?.[0] ?? null;
            setSelectedFile(file);
          }}
        />
        {selectedFile ? <p className="helper-text">Arquivo selecionado: {selectedFile.name}</p> : null}
      </div>

      <form className="stacked-form" onSubmit={handleSubmit}>
        <label>
          Título da apresentação
          <input
            type="text"
            value={form.title}
            onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))}
            placeholder="Pitch de vendas, palestra, entrevista..."
          />
        </label>
        <label>
          Idioma
          <input
            type="text"
            value={form.language}
            onChange={(event) => setForm((current) => ({ ...current, language: event.target.value }))}
            placeholder="pt"
          />
        </label>
        <label>
          Contexto da fala
          <textarea
            rows={4}
            value={form.analysis_goal}
            onChange={(event) => setForm((current) => ({ ...current, analysis_goal: event.target.value }))}
            placeholder="Descreva o objetivo da apresentação e o público."
          />
        </label>
        <button type="submit" disabled={loading}>
          {loading ? 'Enviando...' : 'Enviar para análise'}
        </button>
      </form>

      {error ? <p className="form-error">{error}</p> : null}
    </section>
  );
}
