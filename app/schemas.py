"""Pydantic schema untuk request body dan structured output."""
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


# --------------------------------------------------------------------------- request
class ConceptScore(BaseModel):
    """Hasil satu konsep: berapa soal benar dari total soal."""

    concept: str = Field(..., min_length=2, max_length=80, examples=["Persamaan linear"])
    correct: int = Field(..., ge=0, examples=[3])
    total: int = Field(..., gt=0, le=100, examples=[8])

    @field_validator("concept")
    @classmethod
    def strip_concept(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("nama konsep tidak boleh kosong")
        return v

    @model_validator(mode="after")
    def check_correct_le_total(self):
        if self.correct > self.total:
            raise ValueError(f"'{self.concept}': correct ({self.correct}) tidak boleh lebih besar dari total ({self.total})")
        return self


class AnalyzeRequest(BaseModel):
    """Body untuk POST /analyze."""

    student_label: str = Field("Siswa", max_length=40, description="Nama panggilan / kode siswa (jangan nama lengkap)")
    grade_level: str = Field("SMA kelas 11", max_length=40)
    subject: str = Field("Matematika", max_length=40)
    scores: list[ConceptScore] = Field(..., min_length=1, max_length=15)
    teacher_note: str | None = Field(None, max_length=500, description="Catatan guru (opsional)")

    @model_validator(mode="after")
    def unique_concepts(self):
        names = [s.concept.lower() for s in self.scores]
        if len(names) != len(set(names)):
            raise ValueError("nama konsep tidak boleh duplikat")
        return self


class ExperimentRequest(AnalyzeRequest):
    """Body untuk POST /experiment: input sama + versi prompt."""

    prompt_version: Literal["A", "B", "C"] = "C"


# --------------------------------------------------------------------------- structured output (dari LLM)
Status = Literal["dikuasai", "perlu_latihan", "belum_dikuasai"]


class ConceptStatus(BaseModel):
    konsep: str
    persentase_benar: int = Field(..., ge=0, le=100)
    status: Status


class Recommendation(BaseModel):
    konsep: str
    aktivitas: str = Field(..., description="Aktivitas belajar yang konkret")
    alasan: str = Field(..., description="Kenapa aktivitas ini cocok untuk konsep tersebut")


class LearningGapReport(BaseModel):
    """Structured output yang diminta dari LLM (Prompt C / endpoint /analyze)."""

    ringkasan: str = Field(..., description="2-3 kalimat kondisi belajar siswa")
    status_konsep: list[ConceptStatus]
    konsep_prioritas: list[str] = Field(..., description="Maksimal 3 konsep yang paling perlu dipelajari dulu")
    rekomendasi_belajar: list[Recommendation]
    pesan_untuk_siswa: str = Field(..., description="Pesan singkat yang menyemangati, menyapa 'kamu'")


class AnalyzeResponse(BaseModel):
    """Yang dikembalikan endpoint /analyze ke user."""

    student_label: str
    report: LearningGapReport
    warnings: list[str] = Field(default_factory=list, description="Hal yang dikoreksi oleh validator")
    model: str
    prompt_version: str


class ExperimentResponse(BaseModel):
    prompt_version: str
    system_prompt: str
    user_prompt: str
    raw_output: str
    model: str
