# Split Bill App

## Laporan Benchmark VLM Receipt Parser

### 1. Metodologi
**Model:** `qwen2.5vl:3b` vs `gemma4:e2b`

**Hardware:** AMD Radeon RX 6700 XT via Ollama + ROCm

**Metode Pengujian:**
| Komponen | Detail |
|---|---|
| Image Preprocessing | Resize ke max 1600px, base64 encoding |
| Scoring — Nama | Fuzzy matching via `rapidfuzz` (0.0–1.0) |
| Scoring — Harga/Amount | Exact match (%) |
| Warmup | Text-only call sebelum benchmark untuk menghindari cold start |

**Dataset:** 4 struk dengan karakteristik berbeda:

| # | Restoran | Tantangan Unik |
|---|---|---|
| TC1 | Solaria | Item nama dua baris, *negative rounding* |
| TC2 | Paul Bakery | Duplikasi item tanpa kuantitas |
| TC3 | JCO | Item paket dengan sub-item, PB1 termasuk harga |
| TC4 | HokBen | Foto buram, istilah lokal (Pembulatan) |

**System Prompt:**
```
You are a receipt parser. Extract only the relevant information from the receipt image.

ITEMS:
- An item is anything that was ordered (food, drinks, or services) with a price
- If the same item appears multiple times as separate lines, list each one separately
- Include all items regardless of whether the name appears abbreviated or unusual
- If a line has no price and is at the same indentation level as the previous item,
  consolidate it into the previous item's name
- If a line has no price and is indented beneath the previous item, ignore it

CHARGES:
- A charge is any financial adjustment such as tax, service charge, or discount
- Any line with an explicit amount positioned between Sub Total and Total is a charge
- Only include a charge if it has an explicit amount listed next to it

IGNORE:
- Summary lines: Sub Total, Total, Grand Total, Cash, Change,
  Taxable Amount, Taxable Amt, Before Rounding, Payment
- Restaurant name, address, taglines, cashier info, loyalty points, table numbers
```

---

### 2. Hasil Benchmark

#### Qwen2.5-VL-3B

| Receipt | Time | Item Name | Item Price | Charge Name | Charge Amt |
|---|---|---|---|---|---|
| TC1 — Solaria | 13.08s | 0.96 | 80% | 0.50 | 50% |
| TC2 — Paul Bakery | 5.59s | 0.97 | 100% | 1.00 | 100% |
| TC3 — JCO | 14.38s | 0.80 | 100% | 1.00* | 100%* |
| TC4 — HokBen | 4.93s | 0.69 | 0% | 0.63 | 50% |
| **Rata-rata** | **9.50s** | **0.86** | **70%** | **0.78** | **75%** |

#### Gemma4:e2b

| Receipt | Time | Item Name | Item Price | Charge Name | Charge Amt |
|---|---|---|---|---|---|
| TC1 — Solaria | 24.69s | 0.96 | 100% | 0.50 | 0% |
| TC2 — Paul Bakery | 14.06s | 0.67 | 33% | 0.23 | 0% |
| TC3 — JCO | 12.55s | 0.29 | 0% | 1.00* | 100%* |
| TC4 — HokBen | 13.84s | 0.93 | 100% | 0.00 | 0% |
| **Rata-rata** | **16.29s** | **0.71** | **58%** | **0.43** | **25%** |

*\*TC3 charges adalah artefak scoring — ground truth kosong sehingga false positive tidak terdeteksi.*

#### Perbandingan Akhir

| Metrik | `qwen2.5vl:3b` | `gemma4:e2b` | Pemenang |
|---|---|---|---|
| Avg response time | **9.50s** | 16.29s | Qwen ✅ |
| Avg item name score | **0.86** | 0.71 | Qwen ✅ |
| Avg item price accuracy | **70%** | 58% | Qwen ✅ |
| Avg charge name score | **0.78** | 0.43 | Qwen ✅ |
| Avg charge amount accuracy | **75%** | 25% | Qwen ✅ |

**Qwen unggul di semua 5 metrik.**

---

### 3. Analisis Kegagalan

#### Qwen2.5-VL-3B

| Kasus | Penyebab |
|---|---|
| Kwetiau Seafood \| Goreng terpecah (TC1) | Indentasi dua baris tidak terdeteksi setelah resize |
| Rounding: -6 tidak terdeteksi (TC1) | Nilai terlalu kecil, diabaikan model |
| Siomay price `20000` vs `20002` (TC1) | Detail digit hilang akibat kompresi resize |
| Sub-item JCO terdaftar sebagai item terpisah (TC3) | Rule indentasi tidak cukup efektif |
| Semua harga `0.0` di HokBen (TC4) | Foto asli buram — bukan masalah model/prompt |

#### Gemma4:e2b

| Kasus | Penyebab |
|---|---|
| Summary lines masuk sebagai charges (TC1, TC2, TC3) | *Instruction following* lemah — pola konsisten di 3 dari 4 TC |
| Hanya 3 dari 6 item terdeteksi (TC2) | Model mengabaikan item dengan nama non-standard |
| Item utama JCO tidak terdeteksi (TC3) | Layout dengan banyak sub-item membingungkan model |
| Prompt optimasi memperburuk beberapa skor | *Overcorrection* — menambah rule membuat Gemma lebih agresif mengabaikan konten |

#### Prompt Sensitivity

Temuan penting dari proses optimasi system prompt:

- **Qwen** merespons prompt dengan baik — perbaikan rule meningkatkan skor secara konsisten
- **Gemma** tidak stabil terhadap perubahan prompt — memperbaiki satu kasus sering memperburuk kasus lain, mengindikasikan kelemahan *instruction following* pada model MoE di ukuran parameter kecil

---

### 4. Known Limitations

| Limitasi | Dampak | Status |
|---|---|---|
| Foto buram/resolusi rendah | Harga dan nama item tidak terbaca | Dokumentasi — validasi kualitas gambar diperlukan |
| Item nama multi-baris | Item terpecah, subtotal salah jadi harga | Dokumentasi — butuh post-processing |
| Nilai charges sangat kecil (e.g. -6) | Sering diabaikan model | Dokumentasi |
| False positive charges dari teks deskriptif | Charges tidak ada masuk ke output | Sebagian ditangani via prompt |

---

### 5. Rekomendasi

**Model yang direkomendasikan: `qwen2.5vl:3b`** — lebih cepat, lebih akurat, dan lebih konsisten dalam mengikuti instruksi.

---

## Main App

### 1. Repository Structure

```
smart_split_bill/
├── .dockerignore
├── Dockerfile
├── app/
│   ├── core/
│   │   ├── calculator.py
│   │   └── parser.py
│   ├── pages/
│   │   ├── 1_Upload.py
│   │   ├── 2_Parsed_Results.py
│   │   ├── 3_Claiming.py
│   │   └── 4_Results.py
│   └── Home.py
├── config/
│   └── config.yaml
├── data/
│   ├── receipts/
│   │   ├── bon-solaria.jpg
│   │   ├── bon-paul-bakery.jpg
│   │   ├── bon-jco.jpg
│   │   └── bon-hokben.jpg
│   ├── temp/
│   └── test/
│       └── bon-test.jpg
│
├── requirements.txt
└── README.md
```

### 2. Evaluasi Aplikasi Split Bill

Berdasarkan hasil pengujian secara keseluruhan, aplikasi berjalan dengan sangat baik apabila gambar struk yang diunggah masih berada dalam batasan (*known limitations*) yang telah disebutkan sebelumnya. Fitur-fitur utama seperti ekstraksi harga, alokasi klaim tiap pengguna, hingga perhitungan proporsional untuk biaya tambahan (charges) dapat berfungsi dengan lancar sesuai ekspektasi.

Namun, kendala terkait **pembulatan** (misalnya item *rounding* dengan nilai yang sangat kecil seperti -6 atau istilah lokal yang bervariasi) masih tetap ada dan belum teratasi pada versi aplikasi saat ini. Meskipun demikian, untuk mayoritas penggunaan dengan struk standar yang jelas, aplikasi ini sudah sangat memadai dan siap digunakan.

---

### 3. Tutorial Menjalankan Aplikasi via Docker

Aplikasi ini dapat dijalankan menggunakan Docker. Karena proses ekstraksi (*parsing*) sangat diuntungkan oleh GPU lokal melalui **Ollama**, Docker container ini dirancang untuk hanya membungkus UI Streamlit dan akan berkomunikasi dengan instance Ollama di mesin utama (host) Anda.

#### Langkah 1: Persiapan Ollama & Model Lokal
Sebelum menjalankan container, pastikan Anda telah menginstal [Ollama](https://ollama.com/) di komputer Anda dan mengunduh model Vision Language yang dibutuhkan.
Buka terminal Anda dan jalankan perintah berikut untuk mengunduh model:
```bash
ollama run qwen2.5vl:3b
```
*(Catatan: Anda dapat mengubah jenis model yang digunakan dengan mengedit parameter `model_name` di dalam file `config/config.yaml` dan memastikan model tersebut telah diunduh via Ollama).*

#### Langkah 2: Build Docker Image
Buka terminal di root direktori proyek ini, lalu jalankan perintah:
```bash
docker build -t smart_split_bill .
```

### Langkah 3: Menjalankan Container
Agar container Docker dapat berkomunikasi dengan Ollama yang berjalan di host komputer Anda, Anda perlu meneruskan environment variable `OLLAMA_HOST`.

**Untuk pengguna Windows & Mac:**
```bash
docker run -p 8501:8501 -e OLLAMA_HOST=http://host.docker.internal:11434 smart_split_bill
```

**Untuk pengguna Linux:**
Gunakan opsi `--network host` agar container dapat langsung mengakses localhost mesin utama:
```bash
docker run --network host -e OLLAMA_HOST=http://localhost:11434 smart_split_bill
```

Setelah container berhasil berjalan, buka browser Anda dan akses **http://localhost:8501**.
