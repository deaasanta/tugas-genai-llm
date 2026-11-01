"""Test tanpa API key dan tanpa internet: LLM diganti fungsi palsu (mock).

Jalankan:  pytest -q
"""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import main
from app import llm_client
from app.llm_client import LLMError

client = TestClient(main.app)
SAMPLES = Path(__file__).resolve().parent.parent / "sample_inputs"


def load(name):
    return json.loads((SAMPLES / name).read_text(encoding="utf-8"))


def fake_llm(output: dict):
    async def _gen(system, user, response_schema=None):
        return json.dumps(output)
    return _gen


GOOD = {
    "ringkasan": "Reza kuat di barisan aritmetika tetapi masih kesulitan di trigonometri dan persamaan linear.",
    "status_konsep": [
        {"konsep": "Trigonometri dasar", "persentase_benar": 20, "status": "belum_dikuasai"},
        {"konsep": "Persamaan linear", "persentase_benar": 38, "status": "belum_dikuasai"},
        {"konsep": "Fungsi kuadrat", "persentase_benar": 63, "status": "perlu_latihan"},
        {"konsep": "Limit fungsi", "persentase_benar": 67, "status": "perlu_latihan"},
        {"konsep": "Barisan aritmetika", "persentase_benar": 88, "status": "dikuasai"},
    ],
    "konsep_prioritas": ["Trigonometri dasar", "Persamaan linear", "Fungsi kuadrat"],
    "rekomendasi_belajar": [
        {"konsep": "Trigonometri dasar", "aktivitas": "Kerjakan 10 soal sin/cos sudut istimewa", "alasan": "Dasar untuk limit"},
        {"konsep": "Persamaan linear", "aktivitas": "Ubah 5 soal cerita menjadi persamaan", "alasan": "Sesuai catatan guru"},
        {"konsep": "Fungsi kuadrat", "aktivitas": "Gambar 3 grafik parabola", "alasan": "Memperkuat pemahaman visual"},
    ],
    "pesan_untuk_siswa": "Kamu sudah bagus di barisan aritmetika. Yuk mulai dari trigonometri dasar!",
}


def test_home():
    r = client.get("/")
    assert r.status_code == 200


def test_analyze_ok(monkeypatch):
    monkeypatch.setattr(llm_client, "generate", fake_llm(GOOD))
    r = client.post("/analyze", json=load("1_normal.json"))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["warnings"] == []
    assert len(body["report"]["status_konsep"]) == 5
    assert set(body["report"].keys()) >= {"ringkasan", "status_konsep", "konsep_prioritas", "rekomendasi_belajar", "pesan_untuk_siswa"}


def test_validator_fixes_hallucination(monkeypatch):
    bad = json.loads(json.dumps(GOOD))
    bad["status_konsep"][0]["persentase_benar"] = 50            # angka diubah LLM
    bad["konsep_prioritas"] = ["Matriks", "Barisan aritmetika", "Trigonometri dasar"]  # konsep karangan + sudah dikuasai
    bad["rekomendasi_belajar"].append({"konsep": "Matriks", "aktivitas": "x", "alasan": "y"})
    monkeypatch.setattr(llm_client, "generate", fake_llm(bad))
    body = client.post("/analyze", json=load("1_normal.json")).json()
    rep = body["report"]
    assert rep["konsep_prioritas"] == ["Trigonometri dasar"]
    assert all(r["konsep"] != "Matriks" for r in rep["rekomendasi_belajar"])
    assert {c["konsep"]: c["persentase_benar"] for c in rep["status_konsep"]}["Trigonometri dasar"] == 20
    assert len(body["warnings"]) >= 3


def test_invalid_input_returns_422():
    r = client.post("/analyze", json=load("4_input_tidak_valid.json"))
    assert r.status_code == 422


def test_empty_scores_returns_422():
    r = client.post("/analyze", json={"scores": []})
    assert r.status_code == 422


def test_llm_bad_json_returns_502(monkeypatch):
    async def gen(system, user, response_schema=None):
        return "ini bukan json"
    monkeypatch.setattr(llm_client, "generate", gen)
    r = client.post("/analyze", json=load("1_normal.json"))
    assert r.status_code == 502


def test_llm_error_is_forwarded(monkeypatch):
    async def gen(system, user, response_schema=None):
        raise LLMError("Kuota habis", status_code=429)
    monkeypatch.setattr(llm_client, "generate", gen)
    r = client.post("/analyze", json=load("1_normal.json"))
    assert r.status_code == 429
    assert "Kuota" in r.json()["detail"]


@pytest.mark.parametrize("version", ["A", "B", "C"])
def test_experiment_versions(monkeypatch, version):
    async def gen(system, user, response_schema=None):
        return f"output {version}"
    monkeypatch.setattr(llm_client, "generate", gen)
    payload = load("1_normal.json") | {"prompt_version": version}
    body = client.post("/experiment", json=payload).json()
    assert body["prompt_version"] == version
    assert body["raw_output"] == f"output {version}"
    if version == "C":
        assert "FORMAT OUTPUT" in body["user_prompt"]
    else:
        assert "FORMAT OUTPUT" not in body["user_prompt"]
