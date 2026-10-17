from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.analysis import Analysis
from app.models.analysis_metric import AnalysisMetric
from app.models.report import Report
from app.models.transcript import Transcript
from app.models.user import User
from app.pipelines.language import analyze_transcript
from app.pipelines.synthesis import synthesize_report
from app.schemas.analysis import (
    AnalysisListItem,
    AnalysisReportRequest,
    AnalysisReportResponse,
    CreateAnalysisRequest,
)
from app.services.storage import save_uploaded_file


router = APIRouter(prefix="/api/v1/analyses", tags=["analyses"])


@router.post("", response_model=AnalysisListItem, status_code=status.HTTP_201_CREATED)
def create_analysis(
	payload: CreateAnalysisRequest,
	current_user: User = Depends(get_current_user),
	session: Session = Depends(get_db),
) -> AnalysisListItem:
	analysis = Analysis(
		id=uuid4(),
		user_id=current_user.id,
		title=payload.title,
		status="queued",
		storage_key=payload.storage_key,
		original_filename=payload.original_filename,
		language=payload.language,
		analysis_goal=payload.analysis_goal,
		created_at=datetime.now(UTC),
	)
	session.add(analysis)
	session.commit()
	session.refresh(analysis)
	return AnalysisListItem.model_validate(analysis)


@router.post("/upload", response_model=AnalysisListItem, status_code=status.HTTP_201_CREATED)
def upload_analysis(
	file: UploadFile = File(...),
	title: str = Form(...),
	language: str | None = Form(default=None),
	analysis_goal: str | None = Form(default=None),
	current_user: User = Depends(get_current_user),
	session: Session = Depends(get_db),
) -> AnalysisListItem:
	payload = CreateAnalysisRequest(
		title=title,
		storage_key=save_uploaded_file(file.file, file.filename or "upload.bin"),
		original_filename=file.filename or "upload.bin",
		language=language,
		analysis_goal=analysis_goal,
	)
	analysis = Analysis(
		id=uuid4(),
		user_id=current_user.id,
		title=payload.title,
		status="queued",
		storage_key=payload.storage_key,
		original_filename=payload.original_filename,
		language=payload.language,
		analysis_goal=payload.analysis_goal,
		created_at=datetime.now(UTC),
	)
	session.add(analysis)
	session.commit()
	session.refresh(analysis)
	return AnalysisListItem.model_validate(analysis)


@router.post("/{analysis_id}/report", response_model=AnalysisReportResponse)
def generate_report(
	analysis_id: UUID,
	payload: AnalysisReportRequest,
	current_user: User = Depends(get_current_user),
	session: Session = Depends(get_db),
) -> AnalysisReportResponse:
	statement = select(Analysis).where(
		Analysis.id == analysis_id,
		Analysis.user_id == current_user.id,
	)
	analysis = session.scalar(statement)
	if analysis is None:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Análise não encontrada.",
		)

	segments = payload.segments
	metrics = analyze_transcript(segments)
	report_payload = synthesize_report(metrics)
	text = " ".join(segment["text"] if isinstance(segment, dict) else segment.text for segment in segments)
	transcript = Transcript(
		analysis_id=analysis.id,
		text=text,
		segments_json=[
			segment.model_dump() if hasattr(segment, "model_dump") else segment
			for segment in segments
		],
		language=payload.language or analysis.language,
		provider="voxmind-local",
	)
	analysis_metric = AnalysisMetric(
		analysis_id=analysis.id,
		category="language",
		metrics_json=metrics.model_dump(mode="json"),
	)
	report = Report(
		analysis_id=analysis.id,
		overall_score=report_payload["overall_score"],
		report_json={
			"summary": report_payload["summary"],
			"highlights": report_payload["highlights"],
			"metrics": metrics.model_dump(mode="json"),
		},
		model_name="voxmind-language",
		prompt_version="v1",
	)
	session.add_all([transcript, analysis_metric, report])
	session.commit()
	session.refresh(report)

	return AnalysisReportResponse(
		analysis_id=analysis.id,
		overall_score=report_payload["overall_score"],
		summary=report_payload["summary"],
		highlights=report_payload["highlights"],
		metrics=metrics.model_dump(mode="json"),
	)


@router.get("/{analysis_id}/report", response_model=AnalysisReportResponse)
def get_analysis_report(
	analysis_id: UUID,
	current_user: User = Depends(get_current_user),
	session: Session = Depends(get_db),
) -> AnalysisReportResponse:
	statement = select(Analysis).where(
		Analysis.id == analysis_id,
		Analysis.user_id == current_user.id,
	)
	analysis = session.scalar(statement)
	if analysis is None:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Análise não encontrada.",
		)

	report = session.scalar(select(Report).where(Report.analysis_id == analysis.id))
	if report is None or not isinstance(report.report_json, dict):
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Relatório ainda não gerado para esta análise.",
		)

	return AnalysisReportResponse(
		analysis_id=analysis.id,
		overall_score=float(report.overall_score or 0),
		summary=str(report.report_json.get("summary", "")),
		highlights=list(report.report_json.get("highlights", [])),
		metrics=dict(report.report_json.get("metrics", {})),
	)


@router.get("", response_model=list[AnalysisListItem])
def list_analyses(
	current_user: User = Depends(get_current_user),
	session: Session = Depends(get_db),
) -> list[AnalysisListItem]:
	statement = (
		select(Analysis)
		.where(Analysis.user_id == current_user.id)
		.order_by(Analysis.created_at.desc())
	)
	analyses = session.scalars(statement).all()
	return [AnalysisListItem.model_validate(analysis) for analysis in analyses]


@router.get("/{analysis_id}", response_model=AnalysisListItem)
def get_analysis(
	analysis_id: UUID,
	current_user: User = Depends(get_current_user),
	session: Session = Depends(get_db),
) -> AnalysisListItem:
	statement = select(Analysis).where(
		Analysis.id == analysis_id,
		Analysis.user_id == current_user.id,
	)
	analysis = session.scalar(statement)
	if analysis is None:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Análise não encontrada.",
		)
	return AnalysisListItem.model_validate(analysis)
