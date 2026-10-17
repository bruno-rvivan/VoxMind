from functools import lru_cache
import os
from pathlib import Path

import av

from app.schemas.analysis import TranscriptSegment


class NoSpeechDetectedError(ValueError):
	pass


class NoAudioTrackError(NoSpeechDetectedError):
	pass


@lru_cache(maxsize=2)
def _load_model(model_name: str):
	from faster_whisper import WhisperModel

	return WhisperModel(
		model_name,
		device="cpu",
		compute_type="int8",
		cpu_threads=2,
		num_workers=1,
	)


def transcribe_media(
	media_path: Path,
	language: str | None = None,
) -> tuple[list[TranscriptSegment], str]:
	with av.open(str(media_path), mode="r", metadata_errors="ignore") as container:
		if not container.streams.audio:
			raise NoAudioTrackError(
				"O vídeo não contém áudio. Envie um vídeo com fala ou informe a transcrição manualmente."
			)

	model_name = os.getenv("VOXMIND_WHISPER_MODEL", "tiny")
	model = _load_model(model_name)
	generated_segments, transcription_info = model.transcribe(
		str(media_path),
		language=language,
		beam_size=5,
		vad_filter=True,
	)

	segments = [
		TranscriptSegment(
			start=float(segment.start),
			end=float(segment.end),
			text=segment.text.strip(),
		)
		for segment in generated_segments
		if segment.text.strip() and segment.end > segment.start
	]
	if not segments:
		raise NoSpeechDetectedError("Não foi detectada fala no arquivo enviado.")

	return segments, transcription_info.language
