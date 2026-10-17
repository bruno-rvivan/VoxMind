import re
from collections import Counter
from collections.abc import Iterable, Sequence

from app.schemas.analysis import SpeechMetrics, TranscriptSegment


DEFAULT_FILLER_WORDS = frozenset({"ahn", "ã", "hum", "hmm"})
DEFAULT_PAUSE_THRESHOLD_SECONDS = 0.75
WORD_PATTERN = re.compile(r"[^\W_]+(?:['’][^\W_]+)*", re.UNICODE)


def analyze_transcript(
	segments: Sequence[TranscriptSegment | dict[str, object]],
	*,
	filler_words: Iterable[str] = DEFAULT_FILLER_WORDS,
	pause_threshold_seconds: float = DEFAULT_PAUSE_THRESHOLD_SECONDS,
) -> SpeechMetrics:
	if pause_threshold_seconds <= 0:
		raise ValueError("O limite de pausa deve ser maior que zero.")

	validated_segments = [
		segment
		if isinstance(segment, TranscriptSegment)
		else TranscriptSegment.model_validate(segment)
		for segment in segments
	]
	if not validated_segments:
		return SpeechMetrics(
			word_count=0,
			presentation_duration_seconds=0,
			speaking_time_seconds=0,
			words_per_minute=None,
			articulation_rate_wpm=None,
			pause_threshold_seconds=pause_threshold_seconds,
			pause_count=0,
			total_pause_seconds=0,
			longest_pause_seconds=0,
			filler_word_counts={},
			filler_word_total=0,
			adjacent_repetition_count=0,
		)

	ordered_segments = sorted(validated_segments, key=lambda segment: segment.start)
	intervals: list[list[float]] = []
	for segment in ordered_segments:
		if intervals and segment.start <= intervals[-1][1]:
			intervals[-1][1] = max(intervals[-1][1], segment.end)
		else:
			intervals.append([segment.start, segment.end])

	speaking_time = sum(end - start for start, end in intervals)
	presentation_duration = (
		max(segment.end for segment in ordered_segments)
		- min(segment.start for segment in ordered_segments)
	)
	pauses = [
		intervals[index][0] - intervals[index - 1][1]
		for index in range(1, len(intervals))
		if intervals[index][0] - intervals[index - 1][1]
		>= pause_threshold_seconds
	]

	tokens = [
		token.casefold()
		for segment in ordered_segments
		for token in WORD_PATTERN.findall(segment.text)
	]
	filler_set = {word.casefold() for word in filler_words}
	filler_counts = Counter(token for token in tokens if token in filler_set)
	repetitions = sum(
		previous == current
		for previous, current in zip(tokens, tokens[1:])
	)
	word_count = len(tokens)

	return SpeechMetrics(
		word_count=word_count,
		presentation_duration_seconds=round(presentation_duration, 2),
		speaking_time_seconds=round(speaking_time, 2),
		words_per_minute=(
			round(word_count * 60 / presentation_duration, 2)
			if presentation_duration > 0
			else None
		),
		articulation_rate_wpm=(
			round(word_count * 60 / speaking_time, 2)
			if speaking_time > 0
			else None
		),
		pause_threshold_seconds=pause_threshold_seconds,
		pause_count=len(pauses),
		total_pause_seconds=round(sum(pauses), 2),
		longest_pause_seconds=round(max(pauses, default=0), 2),
		filler_word_counts=dict(sorted(filler_counts.items())),
		filler_word_total=sum(filler_counts.values()),
		adjacent_repetition_count=repetitions,
	)
