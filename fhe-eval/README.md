# fhe-eval

Prototipe **framework lapisan backend FHE** untuk skripsi:

> Pengembang aplikasi fokus pada logika bisnis; backend menyiapkan evaluasi CKKS dan menegakkan standar interaksi.

## Stack (nyata, bisa dijalankan)

| Lapisan | Teknologi |
|---------|-----------|
| Skema FHE | **CKKS** via **TenSEAL** (Microsoft SEAL) |
| Layanan | **FastAPI** + Uvicorn |
| Klien | Python tipis (`client/fhe_client.py`) |
| Uji | **pytest** (engine + API + standar) |

> Catatan proposal: OpenFHE adalah target pustaka utama jangka menengah. Adapter mesin di `engine.py` dipisah agar dapat diganti; implementasi berjalan saat ini memakai TenSEAL agar stack terpasang dan teruji di mesin pengembangan.

## Struktur

```
fhe-eval/
  src/fhe_eval/
    config.py       # profil CKKS tetap
    engine.py       # evaluasi TenSEAL (tanpa secret key di server)
    standards.py    # penegakan kontrak
    schemas.py      # model request/response
    metrics.py
    api/            # FastAPI routes
  client/           # klien aplikasi patuh standar
  tests/            # uji nyata (bukan mock FHE)
  STANDARDS.md      # kontrak interaksi
  requirements.txt
```

## Setup

Butuh **Python 3.10–3.12** (TenSEAL belum menyediakan wheel untuk 3.13/3.14). Di mesin ini dipakai `python3.12`.

```bash
# dari root proposal
/opt/homebrew/bin/python3.12 -m venv .venv
source .venv/bin/activate
pip install -r fhe-eval/requirements.txt

cd fhe-eval
export PYTHONPATH=src
```

## Menjalankan backend

```bash
cd fhe-eval
source ../.venv/bin/activate   # jika venv di root proposal
export PYTHONPATH=src
uvicorn fhe_eval.api.app:app --host 127.0.0.1 --port 8000
```

## Demo skoring linear

Terminal lain:

```bash
cd fhe-eval
source ../.venv/bin/activate
export PYTHONPATH=src
python client/demo_linear_score.py --dim 8
python client/demo_linear_score.py --dim 16
```

## Menjalankan tes

```bash
cd fhe-eval
source ../.venv/bin/activate
export PYTHONPATH=src
pytest -q
```

## Endpoint

| Method | Path | Fungsi |
|--------|------|--------|
| GET | `/v1/context` | Profil parameter + status bind |
| POST | `/v1/context/bind` | Ikat public context (tanpa secret key) |
| POST | `/v1/eval/add` | Penjumlahan dua ciphertext |
| POST | `/v1/eval/mul_plain` | Ciphertext × bobot plaintext |
| POST | `/v1/eval/linear_score` | \(y=w^{\top}x+b\) |
| GET | `/v1/metrics/last` | Metrik evaluasi terakhir |

Detail kontrak: [STANDARDS.md](STANDARDS.md).

## Batasan prototipe

- Dimensi 8 dan 16 saja
- Tanpa bootstrapping
- Weights/bias model diperlakukan publik
- Belum multi-tenant / auth produksi
