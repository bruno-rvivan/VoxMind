from pathlib import Path
from types import SimpleNamespace

import pytest

from app.pipelines import transcription
from app.services.storage import get_uploaded_file_path
from app.pipelines.transcription import NoAudioTrackError


def test_transcribe_media_returns_timed_text_segments(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    calls: dict[str, object] = {}

    class FakeModel:
        def transcribe(self, media_path: str, **kwargs: object):
            calls["media_path"] = media_path
            calls["kwargs"] = kwargs
            return iter([
                SimpleNamespace(start=0.25, end=1.5, text="  Olá, mundo.  "),
                SimpleNamespace(start=1.5, end=1.5, text=""),
            ]), SimpleNamespace(language="pt")

    class VideoWithAudio:
        streams = SimpleNamespace(audio=[object()])

        def __enter__(self):
            return self

        def __exit__(self, *_: object) -> None:
            return None

    monkeypatch.setenv("VOXMIND_WHISPER_MODEL", "tiny")
    monkeypatch.setattr(transcription, "_load_model", lambda _: FakeModel())
    monkeypatch.setattr(transcription.av, "open", lambda *_args, **_kwargs: VideoWithAudio())

    segments, language = transcription.transcribe_media(tmp_path / "speech.mp4", "pt")

    assert language == "pt"
    assert [segment.model_dump() for segment in segments] == [
        {"start": 0.25, "end": 1.5, "text": "Olá, mundo."},
    ]
    assert calls["media_path"] == str(tmp_path / "speech.mp4")
    assert calls["kwargs"] == {"language": "pt", "beam_size": 5, "vad_filter": True}


def test_uploaded_file_path_cannot_escape_storage_root(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("VOXMIND_STORAGE_DIR", str(tmp_path))

    with pytest.raises(ValueError, match="inválido"):
        get_uploaded_file_path("../outside.mp4")


def test_transcribe_media_rejects_video_without_audio(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    class SilentVideo:
        streams = SimpleNamespace(audio=[], video=[object()])

        def __enter__(self):
            return self

        def __exit__(self, *_: object) -> None:
            return None

    monkeypatch.setattr(transcription.av, "open", lambda *_args, **_kwargs: SilentVideo())

    with pytest.raises(NoAudioTrackError, match="não contém áudio"):
        transcription.transcribe_media(tmp_path / "silent-video.mp4")