from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CreateAnalysisRequest(BaseModel):
	title: str = Field(min_length=1, max_length=200)
	storage_key: str = Field(min_length=1, max_length=500)
	original_filename: str = Field(min_length=1, max_length=255)
	language: str | None = Field(default=None, min_length=2, max_length=10)
	analysis_goal: str | None = Field(default=None, max_length=80)

	@field_validator("title", "storage_key", "original_filename")
	@classmethod
	def strip_required_strings(cls, value: str) -> str:
		value = value.strip()
		if not value:
			raise ValueError("Este campo não pode ficar vazio.")
		return value

	@field_validator("analysis_goal")
	@classmethod
	def strip_optional_goal(cls, value: str | None) -> str | None:
		if value is None:
			return None
		value = value.strip()
		return value or None


class AnalysisListItem(BaseModel):
	model_config = ConfigDict(from_attributes=True)

	id: UUID
	title: str
	status: str
	original_filename: str
	duration_seconds: int | None
	language: str | None
	analysis_goal: str | None
	created_at: datetime


class TranscriptSegment(BaseModel):
	start: float = Field(ge=0)
	end: float = Field(gt=0)
	text: str = Field(min_length=1)

	@field_validator("text")
	@classmethod
	def strip_text(cls, value: str) -> str:
		value = value.strip()
		if not value:
			raise ValueError("O texto do segmento não pode ficar vazio.")
		return value

	@model_validator(mode="after")
	def validate_interval(self) -> "TranscriptSegment":
		if self.end <= self.start:
			raise ValueError("O fim do segmento deve ser posterior ao início.")
		return self


class AnalysisReportRequest(BaseModel):
	segments: list[TranscriptSegment | dict[str, object]] = Field(default_factory=list)
	language: str | None = Field(default=None, max_length=10)


class AnalysisReportResponse(BaseModel):
	analysis_id: UUID
	overall_score: float = Field(ge=0, le=100)
	summary: str
	highlights: list[str]
	metrics: dict[str, object]


class SpeechMetrics(BaseModel):
	word_count: int = Field(ge=0)
	presentation_duration_seconds: float = Field(ge=0)
	speaking_time_seconds: float = Field(ge=0)
	words_per_minute: float | None = Field(default=None, ge=0)
	articulation_rate_wpm: float | None = Field(default=None, ge=0)
	pause_threshold_seconds: float = Field(gt=0)
	pause_count: int = Field(ge=0)
	total_pause_seconds: float = Field(ge=0)
	longest_pause_seconds: float = Field(ge=0)
	filler_word_counts: dict[str, int]
	filler_word_total: int = Field(ge=0)
	adjacent_repetition_count: int = Field(ge=0)