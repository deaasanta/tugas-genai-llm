"""Logika deterministik: hitung fakta sebelum ke LLM, cek hasil LLM sesudahnya.

Angka tidak diserahkan ke LLM. Python menghitung persentase dan status,
LLM hanya menjelaskan; validator memastikan LLM tidak mengubahnya.
"""
from app.schemas import AnalyzeRequest, LearningGapReport

MASTERED = 75
NEEDS_PRACTICE = 50
MAX_PRIORITY = 3


def status_of(pct: int) -> str:
    if pct >= MASTERED:
        return "dikuasai"
    if pct >= NEEDS_PRACTICE:
        return "perlu_latihan"
    return "belum_dikuasai"


def compute_facts(req: AnalyzeRequest) -> list[dict]:
    """Persentase & status per konsep, urut dari persentase terendah."""
    facts = []
    for s in req.scores:
        pct = int(100 * s.correct / s.total + 0.5)  # pembulatan biasa (round() Python membulatkan 62,5 ke 62)
        facts.append({
            "konsep": s.concept,
            "benar": s.correct,
            "total_soal": s.total,
            "persentase_benar": pct,
            "status": status_of(pct),
            "bukti_sedikit": s.total < 3,
        })
    return sorted(facts, key=lambda f: f["persentase_benar"])


def _key(name: str) -> str:
    return " ".join(name.lower().split())


def validate_report(report: LearningGapReport, req: AnalyzeRequest) -> tuple[LearningGapReport, list[str]]:
    """Koreksi output LLM agar konsisten dengan FAKTA. Mengembalikan (report_terkoreksi, warnings)."""
    warnings: list[str] = []
    facts = {_key(f["konsep"]): f for f in compute_facts(req)}

    # 1. status_konsep: pakai angka & status dari FAKTA, buang konsep karangan, tambahkan yang terlewat
    fixed_status = []
    seen = set()
    for cs in report.status_konsep:
        f = facts.get(_key(cs.konsep))
        if f is None:
            warnings.append(f"Konsep '{cs.konsep}' tidak ada di input, dihapus dari status_konsep.")
            continue
        if cs.persentase_benar != f["persentase_benar"] or cs.status != f["status"]:
            warnings.append(f"Angka/status '{f['konsep']}' dari LLM ({cs.persentase_benar}%, {cs.status}) "
                            f"dikoreksi menjadi {f['persentase_benar']}%, {f['status']}.")
        seen.add(_key(f["konsep"]))
        fixed_status.append({"konsep": f["konsep"], "persentase_benar": f["persentase_benar"], "status": f["status"]})
    for k, f in facts.items():
        if k not in seen:
            warnings.append(f"Konsep '{f['konsep']}' tidak disebut LLM, ditambahkan dari FAKTA.")
            fixed_status.append({"konsep": f["konsep"], "persentase_benar": f["persentase_benar"], "status": f["status"]})

    # 2. konsep_prioritas: hanya konsep yang ada dan belum dikuasai, maksimal 3
    priority = []
    for name in report.konsep_prioritas:
        f = facts.get(_key(name))
        if f is None:
            warnings.append(f"Konsep prioritas '{name}' tidak ada di input, dihapus.")
        elif f["status"] == "dikuasai":
            warnings.append(f"'{f['konsep']}' sudah dikuasai, dihapus dari konsep_prioritas.")
        elif f["konsep"] not in priority:
            priority.append(f["konsep"])
    if len(priority) > MAX_PRIORITY:
        warnings.append(f"konsep_prioritas dipotong menjadi {MAX_PRIORITY}.")
        priority = priority[:MAX_PRIORITY]

    # 3. rekomendasi: hanya untuk konsep yang ada di input
    recs = []
    for r in report.rekomendasi_belajar:
        f = facts.get(_key(r.konsep))
        if f is None:
            warnings.append(f"Rekomendasi untuk konsep '{r.konsep}' yang tidak ada di input dihapus.")
            continue
        recs.append({"konsep": f["konsep"], "aktivitas": r.aktivitas, "alasan": r.alasan})

    fixed = LearningGapReport(
        ringkasan=report.ringkasan,
        status_konsep=fixed_status,
        konsep_prioritas=priority,
        rekomendasi_belajar=recs,
        pesan_untuk_siswa=report.pesan_untuk_siswa,
    )
    return fixed, warnings
