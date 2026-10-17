export default function LandingPage() {
  return (
    <section className="landing">
      <div className="hero-banner card">
        <div>
          <span className="eyebrow">VoxMind</span>
          <h1>Aprimore sua performance com análise objetiva de fala e presença.</h1>
          <p>
            A plataforma transforma vídeos em métricas claras sobre ritmo, pausas,
            clareza, postura e progresso de apresentação.
          </p>
          <div className="cta-row">
            <button type="button">Experimentar demo</button>
            <button type="button" className="secondary">
              Ver relatório
            </button>
          </div>
        </div>
      </div>

      <div className="feature-grid">
        <article className="card">
          <h3>Ritmo e fluência</h3>
          <p>Identifique pausas, velocidade e repetições que afetam a mensagem.</p>
        </article>
        <article className="card">
          <h3>Clareza verbal</h3>
          <p>Analise uso de palavras de preenchimento e organização da fala.</p>
        </article>
        <article className="card">
          <h3>Presença visual</h3>
          <p>Entenda melhor enquadramento, estabilidade e sinais de comunicação.</p>
        </article>
      </div>
    </section>
  );
}
