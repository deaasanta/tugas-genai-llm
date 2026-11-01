"""System prompt dan tiga versi prompt untuk eksperimen (A, B, C).

Persentase dan status dihitung di Python (lihat analysis.py), bukan oleh LLM,
sehingga LLM hanya menjelaskan dan memberi rekomendasi.
"""
import json

from app.analysis import compute_facts
from app.schemas import AnalyzeRequest

# --------------------------------------------------------------------------- Prompt A: sederhana
SYSTEM_A = "You are a helpful assistant."
TEMPLATE_A = "Analisis nilai siswa ini:\n{scores_plain}"

# --------------------------------------------------------------------------- Prompt B: Role + Task + Context
SYSTEM_B = (
    "Kamu adalah guru matematika berpengalaman yang membantu siswa menemukan konsep yang belum dikuasai "
    "(learning gap)."
)
TEMPLATE_B = (
    "Tugas: analisis hasil tes siswa berikut, tentukan konsep mana yang sudah dikuasai dan mana yang belum, "
    "lalu beri rekomendasi belajar.\n\n"
    "Konteks: siswa {student_label}, {grade_level}, mata pelajaran {subject}. "
    "Catatan guru: {teacher_note}\n\n"
    "Hasil tes per konsep:\n{scores_plain}"
)

# --------------------------------------------------------------------------- Prompt C: Role + Task + Context + Constraint + Output Format
SYSTEM_C = """Kamu adalah guru matematika berpengalaman yang membantu siswa menemukan konsep yang belum dikuasai (learning gap) dan menyusun rencana belajar.

ATURAN WAJIB:
1. HANYA gunakan konsep dan angka yang ada di FAKTA. Jangan menambah konsep baru.
2. Salin persentase_benar dan status dari FAKTA apa adanya. Jangan menghitung ulang atau mengubahnya.
3. konsep_prioritas berisi maksimal 3 konsep berstatus "belum_dikuasai" atau "perlu_latihan", diurutkan dari persentase terendah. Jika semua konsep "dikuasai", isi dengan list kosong.
4. Buat tepat satu rekomendasi untuk setiap konsep di konsep_prioritas. Aktivitas harus konkret (apa yang dikerjakan, berapa soal/menit), bukan saran umum seperti "belajar lebih giat".
5. Jangan memberi label negatif pada siswa (malas, bodoh, lemah). Jangan menjanjikan hasil ("pasti", "dijamin").
6. Gunakan bahasa Indonesia yang sederhana. pesan_untuk_siswa menyapa dengan "kamu", maksimal 2 kalimat.
7. Jika total soal suatu konsep kurang dari 3, sebutkan di ringkasan bahwa bukti untuk konsep itu masih sedikit."""

TEMPLATE_C = """TUGAS:
Buat laporan learning gap untuk satu siswa dari hasil tes per konsep.

KONTEKS:
Siswa: {student_label} | Jenjang: {grade_level} | Mapel: {subject}
Catatan guru: {teacher_note}
Ambang status: >= 75% dikuasai, 50-74% perlu_latihan, < 50% belum_dikuasai (sudah dihitung di FAKTA).

FAKTA (JSON):
{facts_json}

FORMAT OUTPUT:
Kembalikan HANYA JSON valid dengan field:
- ringkasan (string, 2-3 kalimat)
- status_konsep (list of {{konsep, persentase_benar, status}}) untuk SEMUA konsep di FAKTA
- konsep_prioritas (list of string, maks 3)
- rekomendasi_belajar (list of {{konsep, aktivitas, alasan}})
- pesan_untuk_siswa (string)"""

PROMPTS = {
    "A": (SYSTEM_A, TEMPLATE_A),
    "B": (SYSTEM_B, TEMPLATE_B),
    "C": (SYSTEM_C, TEMPLATE_C),
}


def build_prompt(req: AnalyzeRequest, version: str = "C") -> tuple[str, str]:
    """Kembalikan (system_prompt, user_prompt) untuk versi prompt tertentu."""
    system, template = PROMPTS[version]
    facts = compute_facts(req)
    scores_plain = "\n".join(f"- {s.concept}: {s.correct}/{s.total} benar" for s in req.scores)
    user = template.format(
        student_label=req.student_label,
        grade_level=req.grade_level,
        subject=req.subject,
        teacher_note=req.teacher_note or "-",
        scores_plain=scores_plain,
        facts_json=json.dumps(facts, ensure_ascii=False, indent=2),
    )
    return system, user
