# HEBA

**HEBA** (*Homomorphic Encryption Backend Architecture*) — prototipe kerangka **backend evaluasi FHE** dengan standar interaksi bagi pengembang aplikasi.

Pengembang fokus pada logika aplikasi. HEBA menyiapkan evaluasi CKKS, penegakan kontrak, dan metrik layanan.

## Stack

| Lapisan | Teknologi |
|---------|-----------|
| Nama sistem | **HEBA** |
| Skema FHE | CKKS via **TenSEAL** (Microsoft SEAL) |
| Layanan | **FastAPI** + Uvicorn |
| Klien | Python tipis (`client/heba_client.py`) |
| Uji | **pytest** |

Adapter mesin ada di `engine.py` agar dapat diganti (mis. OpenFHE) tanpa mengubah kontrak REST.

## Struktur

```
heba/
  src/heba/         # inti backend
  client/           # klien patuh standar + demo
  tests/
  STANDARDS.md      # kontrak interaksi
  requirements.txt
```

## Setup

Butuh **Python 3.10–3.12** (TenSEAL).

```bash
# dari root proposal
/opt/homebrew/bin/python3.12 -m venv .venv
source .venv/bin/activate
pip install -r heba/requirements.txt

cd heba
export PYTHONPATH=src
```

## Menjalankan backend

```bash
cd heba
source ../.venv/bin/activate
export PYTHONPATH=src
uvicorn heba.api.app:app --host 127.0.0.1 --port 8000
```

## Demo skoring linear

```bash
python client/demo_linear_score.py --dim 8
python client/demo_linear_score.py --dim 16
```

## Tes

```bash
export PYTHONPATH=src
pytest -q
```

## Endpoint

| Method | Path | Fungsi |
|--------|------|--------|
| GET | `/v1/context` | Profil parameter + status bind |
| POST | `/v1/context/bind` | Ikat public context |
| POST | `/v1/eval/add` | Penjumlahan ciphertext |
| POST | `/v1/eval/mul_plain` | Ciphertext × bobot plaintext |
| POST | `/v1/eval/linear_score` | \(y=w^{\top}x+b\) |
| GET | `/v1/metrics/last` | Metrik terakhir |

Detail kontrak: [STANDARDS.md](STANDARDS.md).
