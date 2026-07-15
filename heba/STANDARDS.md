# Standar Interaksi Aplikasi dan Backend HEBA

Dokumen ini adalah kontrak akademik untuk prototipe HEBA. Pengembang aplikasi wajib mematuhinya. Backend menegakkan aturan pada setiap permintaan evaluasi.

## Peran

| Pihak | Boleh | Tidak boleh |
|-------|--------|-------------|
| **Aplikasi / klien** | Generate kunci, enkripsi input, kirim ciphertext, dekripsi hasil | Mengirim secret key ke backend; meminta dekripsi di server |
| **Backend evaluasi** | Simpan public context, evaluasi ciphertext, kembalikan ciphertext | Menyimpan secret key; mengembalikan plaintext hasil |

## Profil konteks aktif

- `context_id`: `ckks-n8192-s40-d8-16`
- Skema: CKKS (TenSEAL / Microsoft SEAL)
- `poly_modulus_degree`: 8192
- `global_scale`: 2^40
- Dimensi vektor diizinkan: **8**, **16**
- Operasi diizinkan: `add`, `mul_plain`, `linear_score`

## Endpoint

### `GET /v1/context`
Mengembalikan profil parameter publik, daftar operasi, dan status binding.

### `POST /v1/context/bind`
Mengikat **public context** (tanpa secret key) ke backend.

```json
{
  "context_id": "ckks-n8192-s40-d8-16",
  "public_context_b64": "<base64 public context>"
}
```

Public context yang masih berisi secret key **ditolak**.

### `POST /v1/eval/add`
```json
{
  "context_id": "ckks-n8192-s40-d8-16",
  "dimension": 8,
  "left_ciphertext_b64": "...",
  "right_ciphertext_b64": "..."
}
```

### `POST /v1/eval/mul_plain`
```json
{
  "context_id": "ckks-n8192-s40-d8-16",
  "dimension": 8,
  "ciphertext_b64": "...",
  "weights": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
}
```

### `POST /v1/eval/linear_score`
Menghitung \(y = \mathbf{w}^{\top}\mathbf{x} + b\) dengan \(\mathbf{x}\) terenkripsi.

```json
{
  "context_id": "ckks-n8192-s40-d8-16",
  "dimension": 8,
  "features_ciphertext_b64": "...",
  "weights": [/* d floats, plaintext publik model */],
  "bias": 0.0
}
```

Pada prototipe ini, `weights` dan `bias` diperlakukan sebagai parameter model publik. Fitur `x` adalah data sensitif klien.

### `GET /v1/metrics/last`
Metrik evaluasi/penolakan terakhir: latensi, ukuran payload, `reject_reason`.

## Aturan penolakan (HTTP 400)

| `reject_reason` | Penyebab |
|-----------------|----------|
| `secret_key_forbidden` | Field `secret_key` ada di body |
| `context_id_mismatch` | `context_id` bukan profil aktif |
| `dimension_not_allowed` | `dimension` di luar {8, 16} |
| `operation_not_allowed` | Operasi di luar whitelist |
| `weights_dimension_mismatch` | Panjang weights ≠ dimension |
| `bind_failed` / `engine_error` | Context tidak valid / evaluasi gagal |

Tidak ada endpoint dekripsi di backend. Keluaran evaluasi selalu ciphertext (Base64).

## Alur pengembang aplikasi yang patuh

1. `GET /v1/context` — pastikan profil.
2. Buat context CKKS di klien (secret key tetap lokal).
3. `POST /v1/context/bind` — kirim public context saja.
4. Enkripsi input di klien.
5. Panggil `/v1/eval/*`.
6. Dekripsi hasil di klien.
7. (Opsional) bandingkan ke baseline plaintext untuk validasi.

## Target akurasi prototipe

Untuk `linear_score` pada profil ini, galat relatif terhadap baseline plaintext ditargetkan **&lt; 1e-3** (karakteristik aproksimasi CKKS).
