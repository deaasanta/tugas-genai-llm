# GenAI Application

> Petunjuk singkat (hapus bagian ini sebelum dikumpulkan): bagian bertanda **[ISI SENDIRI]** wajib diisi dengan
> **output asli** dari aplikasi yang kamu jalankan sendiri, dan jawaban refleksi dengan kata-katamu sendiri.
> Cara menjalankan dan cara melakukan eksperimen ada di bagian paling bawah README ini.

## Project Information

**Nama Project:**
Learning Gap Report Generator

**Use Case:**
Guru/siswa memasukkan hasil tes per konsep matematika (jumlah benar dari total soal). Aplikasi mengembalikan laporan
learning gap terstruktur: status tiap konsep, konsep prioritas, rekomendasi belajar yang konkret, dan pesan untuk siswa.

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

**Penjelasan kalian:**

[ISI SENDIRI — jelaskan alur di atas dengan bahasamu sendiri, termasuk kenapa angka dihitung di Python dan bukan oleh LLM]

## API Endpoint

| Method | Endpoint | Fungsi |
|---|---|---|
| GET | `/` | Cek aplikasi berjalan |
| POST | `/analyze` | **Endpoint utama**: Prompt C + structured output + validator |
| POST | `/experiment` | Menjalankan input yang sama dengan Prompt `A`, `B`, atau `C` dan mengembalikan output mentah (untuk Prompt Experiment) |

**Endpoint kalian:**

`POST /analyze`

## Example Request

[ISI SENDIRI — tempel request yang benar-benar kamu kirim. Bisa memakai `sample_inputs/1_normal.json`]

## Example Response

[ISI SENDIRI — tempel response asli dari `/analyze`]

## Structured Output

```json
{
  "student_label": "string",
  "report": {
    "ringkasan": "string",
    "status_konsep": [
      {"konsep": "string", "persentase_benar": 0, "status": "dikuasai | perlu_latihan | belum_dikuasai"}
    ],
    "konsep_prioritas": ["string"],
    "rekomendasi_belajar": [
      {"konsep": "string", "aktivitas": "string", "alasan": "string"}
    ],
    "pesan_untuk_siswa": "string"
  },
  "warnings": ["string"],
  "model": "string",
  "prompt_version": "C"
}
```

**Kenapa kalian memilih field-field tersebut?**

[ISI SENDIRI — contoh arah jawaban: `status_konsep` untuk guru melihat semua konsep sekaligus; `konsep_prioritas`
dibatasi 3 agar siswa tahu harus mulai dari mana; `rekomendasi_belajar` punya `alasan` agar guru bisa menilai apakah
saran masuk akal; `warnings` agar terlihat kapan LLM salah dan dikoreksi. Tulis ulang dengan kata-katamu.]

## Prompt Experiment

### Input yang Digunakan

[ISI SENDIRI — disarankan `sample_inputs/1_normal.json` untuk ketiga prompt]

### Prompt A

System prompt:

```text
You are a helpful assistant.
```

User prompt (template):

```text
Analisis nilai siswa ini:
{scores_plain}
```

### Actual Output A

[ISI SENDIRI — `raw_output` dari `POST /experiment` dengan `"prompt_version": "A"`]

### Prompt B

System prompt:

```text
Kamu adalah guru matematika berpengalaman yang membantu siswa menemukan konsep yang belum dikuasai (learning gap).
```

User prompt (template):

```text
Tugas: analisis hasil tes siswa berikut, tentukan konsep mana yang sudah dikuasai dan mana yang belum, lalu beri rekomendasi belajar.

Konteks: siswa {student_label}, {grade_level}, mata pelajaran {subject}. Catatan guru: {teacher_note}

Hasil tes per konsep:
{scores_plain}
```

### Actual Output B

[ISI SENDIRI]

### Prompt C

System prompt:

```text
Kamu adalah guru matematika berpengalaman yang membantu siswa menemukan konsep yang belum dikuasai (learning gap) dan menyusun rencana belajar.

ATURAN WAJIB:
1. HANYA gunakan konsep dan angka yang ada di FAKTA. Jangan menambah konsep baru.
2. Salin persentase_benar dan status dari FAKTA apa adanya. Jangan menghitung ulang atau mengubahnya.
3. konsep_prioritas berisi maksimal 3 konsep berstatus "belum_dikuasai" atau "perlu_latihan", diurutkan dari persentase terendah. Jika semua konsep "dikuasai", isi dengan list kosong.
4. Buat tepat satu rekomendasi untuk setiap konsep di konsep_prioritas. Aktivitas harus konkret (apa yang dikerjakan, berapa soal/menit), bukan saran umum seperti "belajar lebih giat".
5. Jangan memberi label negatif pada siswa (malas, bodoh, lemah). Jangan menjanjikan hasil ("pasti", "dijamin").
6. Gunakan bahasa Indonesia yang sederhana. pesan_untuk_siswa menyapa dengan "kamu", maksimal 2 kalimat.
7. Jika total soal suatu konsep kurang dari 3, sebutkan di ringkasan bahwa bukti untuk konsep itu masih sedikit.
```

User prompt (template):

```text
TUGAS:
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
- pesan_untuk_siswa (string)
```

Prompt C juga dikirim dengan `response_schema=LearningGapReport`, sehingga Gemini dipaksa mengembalikan JSON.

### Actual Output C

[ISI SENDIRI]

## Prompt Evaluation

**Dari ketiga prompt tersebut, mana yang menurut kalian menghasilkan output paling baik?**

[ISI SENDIRI]

**Kenapa?**

[ISI SENDIRI]

**Apa perbedaan paling terlihat antara Prompt A, Prompt B, dan Prompt C berdasarkan hasil testing kalian?**

[ISI SENDIRI — perhatikan: format output, apakah angka persentase benar, panjang jawaban, apakah rekomendasi konkret]

## Failure Case

**Input yang menghasilkan output kurang baik**

[ISI SENDIRI — kandidat yang bisa dicoba: `sample_inputs/3_kandidat_failure.json` (catatan guru berisi instruksi
menyesatkan + konsep dengan 1–2 soal saja) atau `sample_inputs/2_semua_dikuasai.json`. Pakai yang benar-benar
menghasilkan output jelek di aplikasimu.]

**Actual Output**

[ISI SENDIRI]

**Menurut kalian apa masalah dari output tersebut?**

[ISI SENDIRI]

**Apa yang kalian ubah pada prompt / constraint / kode?**

[ISI SENDIRI — sebutkan file dan baris yang diubah, misalnya aturan baru di `SYSTEM_C` pada `app/prompts.py`]

**Output setelah diperbaiki**

[ISI SENDIRI — jalankan ulang input yang sama]

## Personal Reflection

**1. Menurut kalian, bagian apa yang paling sulit dari project ini?**

[ISI SENDIRI]

**2. Bagian kode mana yang paling banyak dibantu oleh AI?**

[ISI SENDIRI]

**3. Setelah melihat kode tersebut, jelaskan menggunakan bahasa kalian sendiri bagaimana bagian tersebut bekerja.**

[ISI SENDIRI]

**4. Menurut kalian, apa kekurangan terbesar dari aplikasi yang kalian buat jika digunakan oleh user sungguhan?**

[ISI SENDIRI]

**5. Jika provider LLM kalian diganti, misalnya dari Groq ke Gemini atau OpenAI, bagian mana dari project yang menurut kalian perlu diubah?**

[ISI SENDIRI — petunjuk: semua kode provider ada di `app/llm_client.py`]

**6. Setelah mencoba aplikasi kalian sendiri, apa satu improvement yang menurut kalian paling penting jika project ini dilanjutkan?**

[ISI SENDIRI]

## AI Usage

**AI tools yang digunakan**

[ISI SENDIRI]

**AI digunakan untuk membantu bagian apa?**

[ISI SENDIRI]

**Bagian apa yang kalian tentukan, perbaiki, atau ubah sendiri setelah melihat hasil dari AI?**

[ISI SENDIRI]

---

## Cara Menjalankan

```bash
python -m venv venv
# Windows: venv\Scripts\activate     macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env          # macOS/Linux: cp .env.example .env  → lalu isi GEMINI_API_KEY
fastapi dev main.py             # buka http://127.0.0.1:8000/docs
pytest -q                       # test tanpa API key (LLM di-mock)
```

API key Gemini bisa dibuat gratis di Google AI Studio. Jika model default tidak tersedia di akunmu
(error 404 / "cek nama model"), ganti `GEMINI_MODEL` di `.env`.

## Cara Melakukan Prompt Experiment

1. Buka `/docs` → `POST /experiment` → *Try it out*.
2. Tempel isi `sample_inputs/1_normal.json`, tambahkan `"prompt_version": "A"`, lalu *Execute*.
3. Salin `raw_output` ke README bagian *Actual Output A*.
4. Ulangi dengan `"B"` dan `"C"` tanpa mengubah input lainnya.

## Struktur Project

```
tugas-genai-llm/
├── main.py               # FastAPI app & endpoint
├── app/
│   ├── schemas.py        # Pydantic: request body & structured output
│   ├── prompts.py        # system prompt + Prompt A/B/C
│   ├── analysis.py       # hitung FAKTA + validator output LLM
│   └── llm_client.py     # koneksi Gemini + error handling
├── sample_inputs/        # contoh request (normal, edge case, kandidat failure, input tidak valid)
├── tests/test_api.py     # pytest dengan LLM palsu
├── requirements.txt
├── .env.example          # contoh isi .env (tanpa key asli)
└── .gitignore            # .env dan venv tidak ikut ke GitHub
```
