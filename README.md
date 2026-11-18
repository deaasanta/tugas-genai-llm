# GenAI Application

## Project Information

**Nama Project:**
Learning Gap Report Generator

**Use Case:**
Guru memasukkan hasil tes siswa per konsep matematika (jumlah jawaban benar dari total soal). Aplikasi mengembalikan
laporan learning gap terstruktur: status tiap konsep, konsep prioritas, rekomendasi belajar yang konkret, dan pesan
untuk siswa.

**Deskripsi Singkat:**
Nilai total sering tidak menunjukkan konsep mana yang belum dikuasai siswa. Aplikasi ini menghitung persentase dan status
tiap konsep secara deterministik di Python, lalu meminta Gemini menyusun ringkasan dan rencana belajar dalam format JSON.
Hasil LLM diperiksa oleh validator: angka dan status dikoreksi bila berbeda dari perhitungan, dan konsep yang tidak ada di
input dihapus.

## Tech Stack

- Python 3.13 (minimal 3.10)
- FastAPI (REST API + dokumentasi `/docs`)
- Pydantic v2 (validasi request body dan schema structured output)
- Google Gemini API via SDK `google-genai` (model `gemini-3.1-flash-lite`, bisa diganti lewat `.env`)
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

User mengirim hasil tes per konsep (benar dari total soal) ke `POST /analyze`. FastAPI memvalidasi body dengan Pydantic: jumlah benar tidak boleh melebihi total dan nama konsep tidak boleh dobel, kalau salah langsung dibalas 422. Setelah itu Python menghitung sendiri persentase dan status tiap konsep (FAKTA), lalu FAKTA itu dimasukkan ke prompt C bersama system prompt. Gemini dipanggil dengan `response_schema`, jadi jawabannya dipaksa berbentuk JSON sesuai schema `LearningGapReport`. Terakhir, validator di `app/analysis.py` mencocokkan jawaban Gemini dengan FAKTA: angka yang diubah dikoreksi, konsep yang tidak ada di input dibuang, dan setiap koreksi dicatat di field `warnings`. Angka sengaja dihitung di Python karena LLM bisa salah hitung atau mengarang angka, sedangkan Python selalu konsisten.

## API Endpoint

| Method | Endpoint | Fungsi |
|---|---|---|
| GET | `/` | Cek aplikasi berjalan |
| POST | `/analyze` | **Endpoint utama**: Prompt C + structured output + validator |
| POST | `/experiment` | Menjalankan input yang sama dengan Prompt `A`, `B`, atau `C` dan mengembalikan output mentah (untuk Prompt Experiment) |

**Endpoint kalian:**

`POST /analyze`

## Example Request

Request yang dikirim lewat `/docs` (isi `sample_inputs/1_normal.json`):

```json
{
  "student_label": "Reza",
  "grade_level": "SMA kelas 11",
  "subject": "Matematika",
  "scores": [
    {"concept": "Persamaan linear", "correct": 3, "total": 8},
    {"concept": "Fungsi kuadrat", "correct": 5, "total": 8},
    {"concept": "Trigonometri dasar", "correct": 2, "total": 10},
    {"concept": "Limit fungsi", "correct": 4, "total": 6},
    {"concept": "Barisan aritmetika", "correct": 7, "total": 8}
  ],
  "teacher_note": "Reza sering tidak menyelesaikan soal cerita."
}
```

## Example Response

```json
{
  "student_label": "Reza",
  "report": {
    "ringkasan": "Reza telah menguasai barisan aritmetika, namun masih mengalami kesulitan pada konsep trigonometri dan persamaan linear. Kamu perlu lebih banyak berlatih agar dapat menyelesaikan soal matematika dengan lebih baik.",
    "status_konsep": [
      {
        "konsep": "Trigonometri dasar",
        "persentase_benar": 20,
        "status": "belum_dikuasai"
      },
      {
        "konsep": "Persamaan linear",
        "persentase_benar": 38,
        "status": "belum_dikuasai"
      },
      {
        "konsep": "Fungsi kuadrat",
        "persentase_benar": 63,
        "status": "perlu_latihan"
      },
      {
        "konsep": "Limit fungsi",
        "persentase_benar": 67,
        "status": "perlu_latihan"
      },
      {
        "konsep": "Barisan aritmetika",
        "persentase_benar": 88,
        "status": "dikuasai"
      }
    ],
    "konsep_prioritas": [
      "Trigonometri dasar",
      "Persamaan linear",
      "Fungsi kuadrat"
    ],
    "rekomendasi_belajar": [
      {
        "konsep": "Trigonometri dasar",
        "aktivitas": "Mengerjakan 5 soal dasar identitas trigonometri dalam waktu 30 menit.",
        "alasan": "Latihan berulang membantu memperkuat pemahaman rumus dasar yang belum dikuasai."
      },
      {
        "konsep": "Persamaan linear",
        "aktivitas": "Menyelesaikan 5 soal cerita persamaan linear secara bertahap selama 30 menit.",
        "alasan": "Fokus pada soal cerita dapat membantumu membiasakan diri menerjemahkan kalimat menjadi model matematika."
      },
      {
        "konsep": "Fungsi kuadrat",
        "aktivitas": "Menggambar 3 grafik fungsi kuadrat dari persamaan yang diberikan selama 20 menit.",
        "alasan": "Visualisasi grafik akan memperdalam pemahamanmu mengenai karakteristik fungsi kuadrat."
      }
    ],
    "pesan_untuk_siswa": "Teruslah berlatih secara rutin agar kamu semakin terbiasa mengerjakan berbagai jenis soal. Kamu pasti bisa meningkatkan kemampuan matematika jika dilakukan secara bertahap."
  },
  "warnings": [],
  "model": "gemini-3.1-flash-lite",
  "prompt_version": "C"
}
```

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

- `ringkasan`: guru butuh gambaran cepat kondisi siswa dalam 2-3 kalimat sebelum melihat detail.
- `status_konsep`: menampilkan semua konsep beserta persentase dan statusnya, jadi guru bisa melihat konsep mana yang sudah dan belum dikuasai sekaligus.
- `konsep_prioritas`: dibatasi maksimal 3 supaya siswa tahu harus mulai dari mana, tidak kewalahan.
- `rekomendasi_belajar`: berisi aktivitas konkret dan `alasan`, supaya guru bisa menilai apakah sarannya masuk akal, bukan hanya "belajar lebih giat".
- `pesan_untuk_siswa`: bagian yang bisa langsung dibacakan ke siswa dengan bahasa yang menyemangati.
- `warnings` (di luar laporan LLM): memperlihatkan kapan output LLM salah dan sudah dikoreksi validator.

## Prompt Experiment

### Input yang Digunakan

Ketiga prompt memakai input yang sama, yaitu isi `sample_inputs/1_normal.json` (sama dengan Example Request di atas).

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

```text
Berikut adalah analisis nilai siswa tersebut berdasarkan persentase penguasaan materi:

### 1. Perhitungan Persentase per Materi
Untuk melihat performa, kita ubah nilai pecahan menjadi persentase:

*   **Barisan Aritmetika:** (7/8) × 100% = **87,5%** (Sangat Baik)
*   **Limit Fungsi:** (4/6) × 100% = **66,7%** (Cukup/Baik)
*   **Fungsi Kuadrat:** (5/8) × 100% = **62,5%** (Cukup)
*   **Persamaan Linear:** (3/8) × 100% = **37,5%** (Kurang)
*   **Trigonometri Dasar:** (2/10) × 100% = **20,0%** (Sangat Kurang)

---

### 2. Kesimpulan Analisis

*   **Area Kekuatan (Strong Points):**
    Siswa menunjukkan pemahaman yang sangat baik pada materi **Barisan Aritmetika**. Ini menandakan siswa memiliki logika berpikir yang baik dalam memahami pola matematis. Pemahaman pada materi **Limit Fungsi** juga berada di kategori aman.

*   **Area yang Perlu Perhatian (Need Improvement):**
    *   **Fungsi Kuadrat:** Berada di batas tengah. Siswa kemungkinan sudah paham konsep dasar, namun masih kesulitan saat masuk ke variasi soal yang lebih kompleks.
    *   **Persamaan Linear:** Nilai di bawah 40% menunjukkan adanya miskonsepsi pada dasar-dasar aljabar. Mengingat persamaan linear adalah fondasi untuk materi lain (seperti fungsi kuadrat), ini perlu diperbaiki segera.

*   **Area Kritis (Critical Need):**
    *   **Trigonometri Dasar:** Ini adalah nilai terendah. Ada kemungkinan siswa belum memahami konsep dasar (seperti identitas trigonometri, sudut istimewa, atau penggunaan segitiga siku-siku). Karena skor ini sangat rendah, ini menjadi prioritas utama untuk remedial.

---

### 3. Rekomendasi Tindak Lanjut

1.  **Prioritas Remedial:** Fokuskan sesi belajar tambahan pada **Trigonometri Dasar**. Karena nilainya sangat jauh di bawah rata-rata, siswa kemungkinan besar melewatkan konsep dasar sebelum masuk ke soal latihan.
2.  **Perbaikan Fondasi:** Mengingat **Persamaan Linear** sebagai dasar aljabar nilainya juga rendah, lakukan pengulangan materi aljabar dasar. Jika fondasi aljabar lemah, siswa akan terus kesulitan di materi fungsi kuadrat dan limit.
3.  **Strategi Latihan:**
    *   Gunakan metode *peer tutoring* (tutor sebaya), di mana siswa yang mahir di Barisan Aritmetika bisa membantu siswa tersebut menjelaskan konsep dasar aljabar.
    *   Berikan soal dengan tingkat kesulitan bertahap (dari dasar ke kompleks) khusus untuk Trigonometri dan Persamaan Linear.
4.  **Pertahankan Momentum:** Berikan apresiasi pada materi Barisan Aritmetika agar siswa tetap memiliki motivasi belajar.

**Total Rata-rata Skor:** (3+5+2+4+7) / (8+8+10+6+8) = 21 / 40 = **52,5%**.
Secara keseluruhan, kemampuan siswa masih berada di tingkat menengah ke bawah, sehingga diperlukan penguatan pada konsep-konsep fundamental.
```

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

```text
Halo Reza! Sebagai gurumu, saya sudah menganalisis hasil tes kamu. Secara keseluruhan, kamu sudah memiliki fondasi yang cukup baik, terutama pada pola numerik dan manipulasi aljabar dasar. Namun, ada beberapa celah yang perlu kita perbaiki agar pemahamanmu lebih kokoh.

Berikut adalah analisis mendalam saya:

### 1. Analisis Performa
*   **Area Kekuatan (Sudah Dikuasai):**
    *   **Barisan Aritmetika (87,5%):** Kamu sangat baik dalam memahami pola dan urutan. Ini menunjukkan kemampuan logikamu dalam mengikuti prosedur yang sistematis sudah kuat.
    *   **Limit Fungsi (66,7%):** Meskipun belum sempurna, skor ini menunjukkan kamu mulai paham konsep abstrak tentang pendekatan nilai, yang merupakan prasyarat penting untuk kalkulus.

*   **Area yang Perlu Perbaikan (Learning Gaps):**
    *   **Trigonometri Dasar (20%):** Ini adalah titik terlemah. Kemungkinan besar kamu belum hafal sudut istimewa atau kesulitan menghubungkan konsep segitiga dengan fungsi trigonometri (sin, cos, tan).
    *   **Persamaan Linear (37,5%):** Mengejutkan karena ini adalah materi dasar. Jika kamu sering gagal di soal cerita, kemungkinan kamu kesulitan **menerjemahkan bahasa narasi ke dalam bentuk matematika (pemodelan).**
    *   **Fungsi Kuadrat (62,5%):** Kamu sudah paham cara menghitung, tapi mungkin masih sering keliru di bagian akar-akar atau menggambar grafik.

---

### 2. Diagnosis Masalah: Mengapa Soal Cerita Sulit?
Catatan saya mengenai kesulitanmu di soal cerita sangat berkorelasi dengan hasil **Persamaan Linear**. Banyak siswa mahir menghitung $2x + 5 = 15$, tetapi bingung saat soalnya berbunyi: *"Harga 2 buku dan 5 pensil adalah 15 ribu..."*

**Masalah utamamu bukan di "menghitung", melainkan di "memodelkan".**

---

### 3. Rekomendasi Belajar (Action Plan)

Untuk memperbaiki ini, saya sarankan kamu melakukan langkah berikut:

1.  **Strategi "Ubah Bahasa":**
    *   Setiap mengerjakan soal cerita, jangan langsung menghitung. Latih dirimu untuk menuliskan "Diketahui" dan "Ditanya" secara detail.
    *   Gunakan teknik *highlight* kata kunci (misal: "total" = penjumlahan, "selisih" = pengurangan, "tiap/per" = perkalian/pembagian).

2.  **Perkuat Fondasi Trigonometri:**
    *   Jangan menghafal rumus secara acak. Fokus pada pemahaman **Lingkaran Satuan (Unit Circle)**. Jika kamu paham asal-usul nilai sin/cos dari lingkaran, kamu tidak perlu menghafal banyak angka.

3.  **Metode Latihan "Reverse Engineering":**
    *   Karena kamu kuat di Barisan Aritmetika, cobalah melihat contoh soal Fungsi Kuadrat yang sudah selesai dikerjakan. Tutupi langkah penyelesaiannya, lalu coba tuliskan *logika* di balik setiap langkah tersebut, bukan sekadar angkanya.

4.  **Jadwal Latihan:**
    *   **Minggu ini:** Fokus pada *Trigonometri Dasar* (tonton video visualisasi grafik sin/cos agar lebih paham).
    *   **Minggu depan:** Fokus pada *Pemodelan Matematika* untuk Persamaan Linear. Selesaikan minimal 3 soal cerita setiap hari dengan menuliskan model matematikanya dulu sebelum menghitung.

**Pertanyaan saya untukmu:** Saat mengerjakan soal cerita, apakah kamu merasa bingung di bagian "langkah awal" (membuat persamaan) atau justru sudah dapat persamaannya tapi salah saat menghitung hasilnya? 

Jawab pertanyaan ini, dan kita akan mulai sesi bimbingan berikutnya dari sana!
```

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

```text
{
  "ringkasan": "Reza telah menguasai konsep barisan aritmetika dengan sangat baik. Namun, ada beberapa konsep dasar yang masih memerlukan penguatan agar kamu lebih percaya diri dalam mengerjakan soal.",
  "status_konsep": [
    {
      "konsep": "Trigonometri dasar",
      "persentase_benar": 20,
      "status": "belum_dikuasai"
    },
    {
      "konsep": "Persamaan linear",
      "persentase_benar": 38,
      "status": "belum_dikuasai"
    },
    {
      "konsep": "Fungsi kuadrat",
      "persentase_benar": 63,
      "status": "perlu_latihan"
    },
    {
      "konsep": "Limit fungsi",
      "persentase_benar": 67,
      "status": "perlu_latihan"
    },
    {
      "konsep": "Barisan aritmetika",
      "persentase_benar": 88,
      "status": "dikuasai"
    }
  ],
  "konsep_prioritas": [
    "Trigonometri dasar",
    "Persamaan linear",
    "Fungsi kuadrat"
  ],
  "rekomendasi_belajar": [
    {
      "konsep": "Trigonometri dasar",
      "aktivitas": "Mengerjakan 10 soal dasar tentang perbandingan trigonometri dalam segitiga siku-siku selama 30 menit.",
      "alasan": "Fokus pada pemahaman dasar perbandingan sisi akan membantu meningkatkan kemampuan awal kamu."
    },
    {
      "konsep": "Persamaan linear",
      "aktivitas": "Menyelesaikan 8 soal latihan persamaan linear satu variabel dengan langkah-langkah tertulis.",
      "alasan": "Latihan menulis langkah penyelesaian akan membantu kamu membiasakan diri dengan struktur soal cerita."
    },
    {
      "konsep": "Fungsi kuadrat",
      "aktivitas": "Menggambar grafik dari 5 fungsi kuadrat yang berbeda dalam waktu 40 menit.",
      "alasan": "Memahami visualisasi grafik akan mempermudah kamu saat menghadapi masalah fungsi kuadrat dalam bentuk cerita."
    }
  ],
  "pesan_untuk_siswa": "Kamu telah menunjukkan hasil yang baik di beberapa topik, jadi teruslah semangat belajar. Jangan ragu untuk berlatih sedikit demi sedikit agar konsep yang sulit terasa lebih mudah."
}
```

## Prompt Evaluation

**Dari ketiga prompt tersebut, mana yang menurut kalian menghasilkan output paling baik?**

Prompt C, untuk kebutuhan aplikasi ini. Dari sisi isi analisis, Prompt B memberi diagnosis yang paling dalam, tetapi hasilnya tidak bisa dipakai langsung oleh aplikasi.

**Kenapa?**

Aplikasi ini harus mengembalikan JSON yang bisa diproses kode, dan hanya Prompt C yang menghasilkan JSON valid sesuai schema. Semua angkanya sama persis dengan FAKTA (20, 38, 63, 67, 88), `konsep_prioritas` sudah urut dari persentase terendah, dan setiap rekomendasi punya jumlah soal dan durasi yang jelas, misalnya "10 soal perbandingan trigonometri selama 30 menit". Output A dan B berupa teks markdown panjang yang tidak bisa langsung dipakai aplikasi. Meski begitu, Prompt B lebih baik dalam menghubungkan catatan guru dengan nilai: B menyimpulkan bahwa masalah Reza ada di "memodelkan" soal cerita menjadi persamaan, bukan di menghitung. Prompt C hanya menyinggung soal cerita sekilas di bagian alasan rekomendasi.

**Apa perbedaan paling terlihat antara Prompt A, Prompt B, dan Prompt C berdasarkan hasil testing kalian?**

- **Format:** A dan B berupa teks markdown bebas yang panjang, sedangkan C berupa JSON terstruktur yang jauh lebih pendek.
- **Angka:** A dan B menghitung persentase sendiri dengan desimal (87,5%, 37,5%), dan A bahkan menambahkan rata-rata keseluruhan 52,5% yang tidak diminta. C menyalin angka dari FAKTA tanpa mengubahnya.
- **Konteks:** A tidak menerima nama siswa maupun catatan guru, sehingga analisisnya umum dan rekomendasinya ditujukan ke guru atau kelas (misalnya peer tutoring). B memakai catatan guru dan menyapa Reza langsung, tetapi gayanya seperti chatbot karena menutup dengan pertanyaan balik ke siswa.
- **Rekomendasi:** A dan B masih banyak berisi saran umum seperti "tonton video" atau "pahami lingkaran satuan". C memberi aktivitas yang terukur karena aturan nomor 4 mewajibkan jumlah soal dan waktu.
- **Kekurangan C:** `ringkasan` memakai kata "kamu" padahal ditujukan untuk guru. Masalah ini saya bahas dan perbaiki di bagian Failure Case.

## Failure Case

**Input yang menghasilkan output kurang baik**

Input yang sama dengan Example Request (`sample_inputs/1_normal.json`), dikirim ke `POST /analyze` dengan Prompt C.

**Actual Output**

Potongan response dari `/docs` (field yang bermasalah):

```json
{
  "student_label": "Reza",
  "report": {
    "ringkasan": "Kamu telah menguasai barisan aritmetika dengan baik, namun beberapa konsep lain masih memerlukan fokus lebih. Kamu perlu meningkatkan ketelitian dalam menyelesaikan soal-soal matematika lainnya.",
    "status_konsep": [
      {"konsep": "Trigonometri dasar", "persentase_benar": 20, "status": "belum_dikuasai"},
      {"konsep": "Persamaan linear", "persentase_benar": 38, "status": "belum_dikuasai"},
      {"konsep": "Fungsi kuadrat", "persentase_benar": 63, "status": "perlu_latihan"},
      {"konsep": "Limit fungsi", "persentase_benar": 67, "status": "perlu_latihan"}
    ]
  }
}
```

**Menurut kalian apa masalah dari output tersebut?**

Angka dan status sudah benar, tetapi `ringkasan` bermasalah. Ringkasan seharusnya ditujukan untuk guru, namun Gemini
menyapa siswa dengan "kamu", padahal sapaan "kamu" hanya untuk field `pesan_untuk_siswa`. Isinya juga terlalu umum:
tidak menyebut konsep yang paling lemah (Trigonometri dasar 20% dan Persamaan linear 38%), dan tidak memakai catatan guru
bahwa Reza sering tidak menyelesaikan soal cerita. Guru yang membaca ringkasan ini tidak langsung tahu harus fokus ke mana.
Penyebabnya, prompt C hanya mengatur panjang ringkasan (2-3 kalimat) tanpa menyebut untuk siapa ringkasan itu dan apa
isinya.

Masalah ini bukan kebetulan: kata "kamu" juga muncul di `ringkasan` pada Example Response dan Actual Output C di atas, jadi terjadi di setiap percobaan sebelum perbaikan.

**Apa yang kalian ubah pada prompt / constraint / kode?**

Menambahkan aturan nomor 8 di `SYSTEM_C` pada `app/prompts.py`:

```text
8. ringkasan ditujukan untuk GURU, bukan siswa: sebut siswa dengan namanya (student_label) dan jangan memakai kata "kamu". Sebutkan 1-2 konsep dengan persentase terendah beserta angkanya, dan kaitkan dengan catatan guru jika ada.
```

Kode lain tidak diubah, dan input yang dipakai untuk pengujian ulang sama persis.

**Output setelah diperbaiki**

```json
{
  "student_label": "Reza",
  "report": {
    "ringkasan": "Reza saat ini memiliki kendala pada materi Trigonometri dasar dengan persentase benar 20% dan Persamaan linear sebesar 38%. Mengingat catatan guru mengenai kesulitan menyelesaikan soal cerita, fokus pada dua konsep ini sangat krusial untuk memperkuat pemahaman dasar.",
    "status_konsep": [
      {
        "konsep": "Trigonometri dasar",
        "persentase_benar": 20,
        "status": "belum_dikuasai"
      },
      {
        "konsep": "Persamaan linear",
        "persentase_benar": 38,
        "status": "belum_dikuasai"
      },
      {
        "konsep": "Fungsi kuadrat",
        "persentase_benar": 63,
        "status": "perlu_latihan"
      },
      {
        "konsep": "Limit fungsi",
        "persentase_benar": 67,
        "status": "perlu_latihan"
      },
      {
        "konsep": "Barisan aritmetika",
        "persentase_benar": 88,
        "status": "dikuasai"
      }
    ],
    "konsep_prioritas": [
      "Trigonometri dasar",
      "Persamaan linear",
      "Fungsi kuadrat"
    ],
    "rekomendasi_belajar": [
      {
        "konsep": "Trigonometri dasar",
        "aktivitas": "Mengerjakan 5 soal dasar identitas trigonometri selama 30 menit setiap hari.",
        "alasan": "Latihan berulang membantu memperkuat pemahaman konsep dasar yang belum dikuasai."
      },
      {
        "konsep": "Persamaan linear",
        "aktivitas": "Membaca soal cerita, menuliskan variabel, lalu mengubahnya menjadi model matematika selama 20 menit.",
        "alasan": "Aktivitas ini melatih keterbiasaan untuk mengurai soal cerita agar lebih mudah diselesaikan."
      },
      {
        "konsep": "Fungsi kuadrat",
        "aktivitas": "Mengerjakan 3 soal latihan menentukan titik puncak fungsi kuadrat selama 15 menit.",
        "alasan": "Fokus pada satu sub-topik membantu memperbaiki pemahaman secara bertahap."
      }
    ],
    "pesan_untuk_siswa": "Kamu sudah berhasil menguasai materi barisan aritmetika dengan sangat baik. Ayo pelan-pelan kita latih konsep lainnya supaya kamu lebih percaya diri dalam belajar matematika."
  },
  "warnings": [],
  "model": "gemini-3.1-flash-lite",
  "prompt_version": "C"
}
```

## Personal Reflection

**1. Menurut kalian, bagian apa yang paling sulit dari project ini?**

Bagian paling sulit justru di luar kode, yaitu menjalankan dan mengunggah project. Saat push pertama, file ternyata berada di sub-folder dengan nama yang sama karena hasil ekstrak zip, sehingga `main.py` tidak berada di root repo dan saya harus membuat ulang repository git di folder yang benar. Saya juga menemukan folder user di laptop saya ternyata sudah menjadi repository git, sehingga VS Code membaca ribuan file pribadi sebagai perubahan. Dari situ saya belajar selalu mengecek `git status` sebelum commit.

**2. Bagian kode mana yang paling banyak dibantu oleh AI?**

Hampir seluruh kode dibuat dengan bantuan AI (Claude), terutama `app/analysis.py` (perhitungan FAKTA dan validator), `app/llm_client.py` (koneksi ke Gemini dan error handling), dan `tests/test_api.py`.

**3. Setelah melihat kode tersebut, jelaskan menggunakan bahasa kalian sendiri bagaimana bagian tersebut bekerja.**

`compute_facts()` di `app/analysis.py` menghitung persentase benar tiap konsep, misalnya 3 dari 8 soal menjadi 38%, lalu memberi status: 75% ke atas `dikuasai`, 50-74% `perlu_latihan`, di bawah 50% `belum_dikuasai`. Hasil ini dikirim ke Gemini sebagai FAKTA. Setelah Gemini menjawab, `validate_report()` memeriksa ulang jawabannya: kalau Gemini menulis persentase atau status yang berbeda, nilainya diganti dengan FAKTA; kalau Gemini menyebut konsep yang tidak ada di input (misalnya karena perintah di catatan guru), konsep itu dihapus dari prioritas dan rekomendasi; kalau prioritas lebih dari 3, dipotong. Setiap perubahan ditulis di `warnings` supaya terlihat apa saja yang dikoreksi.

**4. Menurut kalian, apa kekurangan terbesar dari aplikasi yang kalian buat jika digunakan oleh user sungguhan?**

Validator hanya bisa memeriksa angka dan nama konsep, tidak bisa menilai apakah rekomendasi belajarnya benar secara pedagogis. Jadi rekomendasi yang terdengar meyakinkan tetap bisa kurang tepat dan masih perlu dicek guru. Selain itu aplikasi bergantung penuh pada API Gemini: kalau kuota habis atau internet mati, laporan tidak bisa dibuat sama sekali, dan input nilai masih harus diketik manual dalam format JSON. Saya juga melihat langsung keterbatasan ini saat testing: `pesan_untuk_siswa` pada Example Response berisi "Kamu pasti bisa...", padahal aturan nomor 5 di prompt melarang kata "pasti", dan validator tidak menangkapnya karena hanya memeriksa angka dan nama konsep, bukan isi teks.

**5. Jika provider LLM kalian diganti, misalnya dari Groq ke Gemini atau OpenAI, bagian mana dari project yang menurut kalian perlu diubah?**

Cukup `app/llm_client.py`, karena hanya file itu yang memanggil SDK Gemini (membuat client, mengirim prompt, menangani error). Yang perlu diubah: library di `requirements.txt`, nama variabel API key di `.env`, cara memanggil model, dan cara meminta output JSON, karena tiap provider punya cara berbeda untuk structured output. `main.py`, `prompts.py`, `schemas.py`, dan `analysis.py` tidak perlu diubah.

**6. Setelah mencoba aplikasi kalian sendiri, apa satu improvement yang menurut kalian paling penting jika project ini dilanjutkan?**

Membuat frontend sederhana berupa form atau upload file nilai (CSV), supaya guru tidak perlu menulis JSON secara manual. Saat ini aplikasi hanya bisa dicoba lewat `/docs`, yang sulit dipakai oleh guru.

## AI Usage

**AI tools yang digunakan**

Claude (Anthropic).

**AI digunakan untuk membantu bagian apa?**

Membuat struktur project dan seluruh kode awal (FastAPI, schema Pydantic, prompt A/B/C, validator, test), template README, script `fill_readme.py` untuk mengambil output aktual, serta panduan langkah demi langkah untuk menjalankan project dan push ke GitHub.

**Bagian apa yang kalian tentukan, perbaiki, atau ubah sendiri setelah melihat hasil dari AI?**

Saya menjalankan project sendiri di laptop, membuat API key Gemini dan mengisinya di `.env`, lalu mencoba endpoint lewat `/docs`. Saat melihat output aktual, saya menemukan bahwa `ringkasan` menyapa siswa dengan "kamu" padahal ringkasan ditujukan untuk guru, lalu saya menambahkan aturan nomor 8 di `SYSTEM_C` (`app/prompts.py`) dan menjalankan ulang input yang sama. Saya juga memperbaiki struktur repository saat push karena file berada di sub-folder hasil ekstrak zip.

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

API key Gemini bisa dibuat gratis di Google AI Studio (https://aistudio.google.com/apikey). Jika model default tidak
tersedia di akunmu (error 404 / "cek nama model"), ganti `GEMINI_MODEL` di `.env`.

## Cara Melakukan Prompt Experiment

Dengan server berjalan, jalankan `python fill_readme.py` di terminal kedua. Script mengirim `sample_inputs/1_normal.json`
ke `POST /analyze` dan ke `POST /experiment` dengan prompt A, B, dan C, lalu menyimpan output aslinya ke README dan ke
`experiment_log.json`. Setelah perbaikan prompt, `python fill_readme.py --after` menjalankan ulang input failure case.

Cara manual: buka `/docs` → `POST /experiment` → *Try it out*, tempel isi `sample_inputs/1_normal.json`, tambahkan
`"prompt_version": "A"`, lalu *Execute*. Ulangi dengan `"B"` dan `"C"`.

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
├── fill_readme.py        # mengambil output aktual dari aplikasi yang berjalan dan mengisinya ke README
├── experiment_log.json   # output mentah hasil fill_readme.py (bukti eksperimen)
├── requirements.txt
├── .env.example          # contoh isi .env (tanpa key asli)
└── .gitignore            # .env dan venv tidak ikut ke GitHub
```