"""Learning Gap Report Generator - FastAPI + Gemini.

Jalankan:  fastapi dev main.py   lalu buka http://127.0.0.1:8000/docs
"""
from fastapi import FastAPI, HTTPException
from pydantic import ValidationError

from app import llm_client
from app.analysis import validate_report
from app.llm_client import LLMError
from app.prompts import build_prompt
from app.schemas import (AnalyzeRequest, AnalyzeResponse, ExperimentRequest, ExperimentResponse,
                         LearningGapReport)

app = FastAPI(
    title="Learning Gap Report Generator",
    description="Mengubah hasil tes per konsep menjadi laporan learning gap dan rencana belajar (JSON).",
    version="1.0.0",
)


@app.get("/")
def home():
    return {"message": "Learning Gap Report Generator is running", "docs": "/docs", "model": llm_client.MODEL}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    """Endpoint utama: Prompt C + structured output + validator."""
    system, user = build_prompt(request, "C")
    try:
        raw = await llm_client.generate(system, user, response_schema=LearningGapReport)
        report = LearningGapReport.model_validate_json(raw)
    except LLMError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=502, detail=f"Output LLM tidak sesuai schema: {e.errors()[:3]}")

    report, warnings = validate_report(report, request)
    return AnalyzeResponse(student_label=request.student_label, report=report, warnings=warnings,
                           model=llm_client.MODEL, prompt_version="C")


@app.post("/experiment", response_model=ExperimentResponse)
async def experiment(request: ExperimentRequest):
    """Untuk Prompt Experiment: jalankan input yang sama dengan prompt A, B, atau C dan lihat output mentahnya.

    Prompt A dan B sengaja TIDAK memakai response_schema, supaya terlihat bedanya dengan prompt C.
    """
    system, user = build_prompt(request, request.prompt_version)
    schema = LearningGapReport if request.prompt_version == "C" else None
    try:
        raw = await llm_client.generate(system, user, response_schema=schema)
    except LLMError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    return ExperimentResponse(prompt_version=request.prompt_version, system_prompt=system, user_prompt=user,
                              raw_output=raw, model=llm_client.MODEL)
