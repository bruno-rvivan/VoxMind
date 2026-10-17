import pytest
from pydantic import ValidationError

from app.pipelines.language import analyze_transcript


def test_analyze_transcript_calculates_speech_metrics() -> None:
	metrics = analyze_transcript(
		[
			{"start": 0, "end": 2, "text": "Olá, ahn eu eu"},
			{"start": 3, "end": 5, "text": "vamos começar."},
		]
	)

	assert metrics.word_count == 6
	assert metrics.presentation_duration_seconds == 5
	assert metrics.speaking_time_seconds == 4
	assert metrics.words_per_minute == 72
	assert metrics.articulation_rate_wpm == 90
	assert metrics.pause_count == 1
	assert metrics.total_pause_seconds == 1
	assert metrics.longest_pause_seconds == 1
	assert metrics.filler_word_counts == {"ahn": 1}
	assert metrics.adjacent_repetition_count == 1


def test_analyze_transcript_merges_overlapping_segments() -> None:
	metrics = analyze_transcript(
		[
			{"start": 0, "end": 2, "text": "Esta é a primeira parte"},
			{"start": 1, "end": 3, "text": "esta é a parte sobreposta"},
			{"start": 3.5, "end": 4.5, "text": "e a última"},
		]
	)

	assert metrics.speaking_time_seconds == 4
	assert metrics.pause_count == 0


def test_analyze_transcript_handles_empty_input() -> None:
	metrics = analyze_transcript([])

	assert metrics.word_count == 0
	assert metrics.words_per_minute is None
	assert metrics.articulation_rate_wpm is None


def test_transcript_segment_rejects_invalid_interval() -> None:
	with pytest.raises(ValidationError):
		analyze_transcript([{"start": 2, "end": 2, "text": "fala"}])