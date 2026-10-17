from __future__ import annotations

from app.schemas.analysis import SpeechMetrics


def synthesize_report(metrics: SpeechMetrics) -> dict[str, object]:
    filler_total = metrics.filler_word_total
    pause_penalty = min(25.0, metrics.pause_count * 6.0)
    filler_penalty = min(20.0, filler_total * 3.0)
    repetition_penalty = min(15.0, metrics.adjacent_repetition_count * 5.0)
    score = 100.0 - pause_penalty - filler_penalty - repetition_penalty

    if metrics.words_per_minute is not None:
        if metrics.words_per_minute < 100 or metrics.words_per_minute > 180:
            score -= 10.0

    score = max(0.0, min(100.0, round(score, 2)))

    highlights = [
        "A fala foi estruturada e tem potencial para melhorar a clareza.",
        "Pausas e repetições devem ser reduzidas para aumentar a fluidez.",
        "A presença verbal pode ser reforçada com exemplos e objetivos mais claros.",
    ]

    if metrics.pause_count == 0:
        highlights[1] = "As pausas foram bem controladas ao longo da apresentação."
    if filler_total == 0:
        highlights[2] = "Não houve uso expressivo de palavras de preenchimento na amostra."
    if metrics.adjacent_repetition_count == 0:
        highlights[0] = "A mensagem teve boa continuidade sem repetições adjacentes e repetição de ideias."

    summary = (
        "A apresentação demonstra boa intenção e estrutura, com necessidade de reduzir pausas "
        "e repetições para aumentar a fluidez e a confiança."
    )

    return {
        "overall_score": score,
        "summary": summary,
        "highlights": highlights,
    }
