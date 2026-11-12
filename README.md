# GenAI Application

**Deskripsi Singkat:**
Nilai total sering tidak menunjukkan konsep mana yang belum dikuasai siswa. Aplikasi ini menghitung persentase dan status
tiap konsep secara deterministik di Python, lalu meminta Gemini menyusun ringkasan dan rencana belajar dalam format JSON.
Hasil LLM diperiksa oleh validator: angka dan status dikoreksi bila berbeda dari perhitungan, dan konsep yang tidak ada di
input dihapus.

## Tech Stack

- Python 3.10+
- FastAPI (REST API + dokumentasi `/docs`)
- Pydantic v2 (validasi request body dan schema structured output)
- Google Gemini API via SDK `google-genai` (model default `gemini-3.1-flash-lite`, bisa diganti lewat `.env`)
- python-dotenv (membaca API key dari `.env`)
- pytest + FastAPI TestClient (test tanpa memanggil LLM)

## Application Flow

```
User Input (JSON hasil tes per konsep)
↓
FastAPI  ── validasi Pydantic (correct ≤ total, konsep tidak duplikat) → 422 bila tidak valid
↓
Python   ── hitung persentase & status tiap konsep (FAKTA), susun system prompt + user prompt
↓
LLM API  ── Gemini dengan response_schema = LearningGapReport (dipaksa JSON)
↓
Validator ── samakan angka/status dengan FAKTA, hapus konsep karangan, batasi prioritas maks. 3
↓
Structured Output (JSON + daftar warnings bila ada yang dikoreksi)
```
