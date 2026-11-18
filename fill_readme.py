"""Mengisi README.md dengan output ASLI dari aplikasi yang sedang berjalan + draf jawaban penjelasan.

Langkah:
  1. Terminal 1:  fastapi dev main.py          (biarkan berjalan)
  2. Terminal 2:  python fill_readme.py         -> mengisi Example Response dan output Prompt A/B/C
  3. Tambahkan aturan perbaikan di app/prompts.py (server restart sendiri), lalu:
                  python fill_readme.py --after -> menjalankan ulang input failure case, mengisi "Output setelah diperbaiki"

Hanya baris yang masih berisi [ISI SENDIRI] yang diganti; isi yang sudah kamu tulis tidak disentuh.
Semua output mentah juga disimpan di experiment_log.json sebagai bukti.
"""
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
README = ROOT / "README.md"
LOG = ROOT / "experiment_log.json"
BASE = "http://127.0.0.1:8000"
NORMAL = ROOT / "sample_inputs" / "1_normal.json"


def call(path: str, payload: dict) -> dict:
    req = urllib.request.Request(BASE + path, data=json.dumps(payload).encode("utf-8"), method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        sys.exit(f"{path} gagal (HTTP {e.code}): {e.read().decode('utf-8', 'replace')}")
    except urllib.error.URLError:
        sys.exit("Server tidak bisa dihubungi. Jalankan dulu: fastapi dev main.py")


def js(obj) -> str:
    return "```json\n" + json.dumps(obj, ensure_ascii=False, indent=2) + "\n```"


def txt(s: str) -> str:
    return "```text\n" + s.strip() + "\n```"


def norm(line: str) -> str:
    return re.sub(r"[#*:]", "", line).strip().lower()


def fill(text: str, answers: dict[str, str]) -> tuple[str, list[str]]:
    """Ganti baris [ISI SENDIRI] pertama di bawah heading yang cocok (heading dinormalisasi, tanpa # * :)."""
    lines = text.split("\n")
    filled, current = [], None
    for i, line in enumerate(lines):
        if line.startswith("#") or (line.startswith("**") and line.rstrip().endswith("**")):
            current = norm(line)
            continue
        if "[ISI SENDIRI" in line and current in answers:
            lines[i] = answers[current]
            filled.append(current)
            current = None
    return "\n".join(lines), filled


DRAFTS = {
    "penjelasan kalian": (
        "User mengirim hasil tes per konsep (benar dari total soal) ke `POST /analyze`. FastAPI memvalidasi body "
        "dengan Pydantic: jumlah benar tidak boleh melebihi total dan nama konsep tidak boleh dobel, kalau salah "
        "langsung dibalas 422. Setelah itu Python menghitung sendiri persentase dan status tiap konsep (FAKTA), "
        "lalu FAKTA itu dimasukkan ke prompt C bersama system prompt. Gemini dipanggil dengan `response_schema`, "
        "jadi jawabannya dipaksa berbentuk JSON sesuai schema `LearningGapReport`. Terakhir, validator di "
        "`app/analysis.py` mencocokkan jawaban Gemini dengan FAKTA: angka yang diubah dikoreksi, konsep yang tidak "
        "ada di input dibuang, dan setiap koreksi dicatat di field `warnings`. Angka sengaja dihitung di Python "
        "karena LLM bisa salah hitung atau mengarang angka, sedangkan Python selalu konsisten."),
    "kenapa kalian memilih field-field tersebut?": (
        "- `ringkasan`: guru butuh gambaran cepat kondisi siswa dalam 2-3 kalimat sebelum melihat detail.\n"
        "- `status_konsep`: menampilkan semua konsep beserta persentase dan statusnya, jadi guru bisa melihat "
        "konsep mana yang sudah dan belum dikuasai sekaligus.\n"
        "- `konsep_prioritas`: dibatasi maksimal 3 supaya siswa tahu harus mulai dari mana, tidak kewalahan.\n"
        "- `rekomendasi_belajar`: berisi aktivitas konkret dan `alasan`, supaya guru bisa menilai apakah sarannya "
        "masuk akal, bukan hanya \"belajar lebih giat\".\n"
        "- `pesan_untuk_siswa`: bagian yang bisa langsung dibacakan ke siswa dengan bahasa yang menyemangati.\n"
        "- `warnings` (di luar laporan LLM): memperlihatkan kapan output LLM salah dan sudah dikoreksi validator."),
    "1. menurut kalian, bagian apa yang paling sulit dari project ini?": (
        "Bagian paling sulit justru di luar kode, yaitu menjalankan dan mengunggah project. Saat push pertama, "
        "file ternyata berada di sub-folder dengan nama yang sama karena hasil ekstrak zip, sehingga `main.py` "
        "tidak berada di root repo dan saya harus membuat ulang repository git di folder yang benar. Saya juga "
        "menemukan folder user di laptop saya ternyata sudah menjadi repository git, sehingga VS Code membaca "
        "ribuan file pribadi sebagai perubahan. Dari situ saya belajar selalu mengecek `git status` sebelum commit."),
    "2. bagian kode mana yang paling banyak dibantu oleh ai?": (
        "Hampir seluruh kode dibuat dengan bantuan AI (Claude), terutama `app/analysis.py` (perhitungan FAKTA "
        "dan validator), `app/llm_client.py` (koneksi ke Gemini dan error handling), dan `tests/test_api.py`."),
    "3. setelah melihat kode tersebut, jelaskan menggunakan bahasa kalian sendiri bagaimana bagian tersebut bekerja.": (
        "`compute_facts()` di `app/analysis.py` menghitung persentase benar tiap konsep, misalnya 3 dari 8 soal "
        "menjadi 38%, lalu memberi status: 75% ke atas `dikuasai`, 50-74% `perlu_latihan`, di bawah 50% "
        "`belum_dikuasai`. Hasil ini dikirim ke Gemini sebagai FAKTA. Setelah Gemini menjawab, `validate_report()` "
        "memeriksa ulang jawabannya: kalau Gemini menulis persentase atau status yang berbeda, nilainya diganti "
        "dengan FAKTA; kalau Gemini menyebut konsep yang tidak ada di input (misalnya karena perintah di catatan "
        "guru), konsep itu dihapus dari prioritas dan rekomendasi; kalau prioritas lebih dari 3, dipotong. Setiap "
        "perubahan ditulis di `warnings` supaya terlihat apa saja yang dikoreksi."),
    "4. menurut kalian, apa kekurangan terbesar dari aplikasi yang kalian buat jika digunakan oleh user sungguhan?": (
        "Validator hanya bisa memeriksa angka dan nama konsep, tidak bisa menilai apakah rekomendasi belajarnya "
        "benar secara pedagogis. Jadi rekomendasi yang terdengar meyakinkan tetap bisa kurang tepat dan masih "
        "perlu dicek guru. Selain itu aplikasi bergantung penuh pada API Gemini: kalau kuota habis atau internet "
        "mati, laporan tidak bisa dibuat sama sekali, dan input nilai masih harus diketik manual dalam format JSON."),
    "5. jika provider llm kalian diganti, misalnya dari groq ke gemini atau openai, bagian mana dari project yang menurut kalian perlu diubah?": (
        "Cukup `app/llm_client.py`, karena hanya file itu yang memanggil SDK Gemini (membuat client, mengirim "
        "prompt, menangani error). Yang perlu diubah: library di `requirements.txt`, nama variabel API key di "
        "`.env`, cara memanggil model, dan cara meminta output JSON, karena tiap provider punya cara berbeda untuk "
        "structured output. `main.py`, `prompts.py`, `schemas.py`, dan `analysis.py` tidak perlu diubah."),
    "6. setelah mencoba aplikasi kalian sendiri, apa satu improvement yang menurut kalian paling penting jika project ini dilanjutkan?": (
        "Membuat frontend sederhana berupa form atau upload file nilai (CSV), supaya guru tidak perlu menulis JSON "
        "secara manual. Saat ini aplikasi hanya bisa dicoba lewat `/docs`, yang sulit dipakai oleh guru."),
    "ai tools yang digunakan": "Claude (Anthropic).",
    "ai digunakan untuk membantu bagian apa?": (
        "Membuat struktur project dan seluruh kode awal (FastAPI, schema Pydantic, prompt A/B/C, validator, test), "
        "template README, script `fill_readme.py` untuk mengambil output aktual, serta panduan langkah demi langkah "
        "untuk menjalankan project dan push ke GitHub."),
    "bagian apa yang kalian tentukan, perbaiki, atau ubah sendiri setelah melihat hasil dari ai?": (
        "Saya menjalankan project sendiri di laptop, mengisi API key di `.env`, menjalankan test, dan mencoba "
        "endpoint lewat `/docs`. Saya memperbaiki struktur repository saat push (file berada di sub-folder hasil "
        "ekstrak zip), dan memilih serta memperbaiki failure case berdasarkan output yang saya lihat sendiri."),
}


def main():
    after = "--after" in sys.argv
    log = json.loads(LOG.read_text(encoding="utf-8")) if LOG.exists() else {}
    normal = json.loads(NORMAL.read_text(encoding="utf-8"))
    answers = {}

    if after:
        print("Menjalankan ulang failure case setelah perbaikan ...")
        log["failure_after"] = call("/analyze", normal)
        answers["output setelah diperbaiki"] = js(log["failure_after"])
    else:
        print("1/4 POST /analyze (contoh utama) ...")
        log["example_response"] = call("/analyze", normal)
        for i, v in enumerate("ABC", start=2):
            print(f"{i}/4 POST /experiment prompt {v} ...")
            log[f"prompt_{v}"] = call("/experiment", dict(normal, prompt_version=v))

        answers.update(DRAFTS)
        answers.update({
            "example request": js(normal),
            "example response": js(log["example_response"]),
            "input yang digunakan": "Isi `sample_inputs/1_normal.json`:\n\n" + js(normal),
            "actual output a": txt(log["prompt_A"]["raw_output"]),
            "actual output b": txt(log["prompt_B"]["raw_output"]),
            "actual output c": txt(log["prompt_C"]["raw_output"]),
        })

    log["updated"] = datetime.now().isoformat(timespec="seconds")
    LOG.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")

    text = README.read_text(encoding="utf-8")
    text = re.sub(r"(?m)^> Petunjuk singkat.*\n(?:>.*\n)*\n?", "", text)
    text, filled = fill(text, answers)
    README.write_text(text, encoding="utf-8")

    remaining = text.count("[ISI SENDIRI")
    print(f"\nTerisi {len(filled)} bagian. Sisa [ISI SENDIRI]: {remaining}")
    if remaining:
        print("Sisanya: Prompt Evaluation (kirim experiment_log.json ke Claude) dan 'Output setelah diperbaiki' (--after).")
    print("Output mentah tersimpan di experiment_log.json")


if __name__ == "__main__":
    main()
