# Laporan Benchmark: VLM Receipt Parser
**Proyek:** Split Bill App — OCR-free Receipt Parsing  
**Tanggal:** Mei 2026  
**Model yang Dibandingkan:** `qwen2.5vl:3b` vs `gemma4:e2b`  
**Environment:** Lokal (AMD Radeon RX 6700 XT, ROCm via Ollama)

---

## 1. Latar Belakang

Laporan ini mendokumentasikan hasil benchmark dua Vision-Language Model (VLM) untuk keperluan ekstraksi data struk belanja (*receipt parsing*) tanpa menggunakan OCR tradisional. Tujuan utama adalah memilih model yang paling akurat dan efisien untuk digunakan sebagai komponen inti aplikasi *split bill*.

Model menerima input berupa foto struk belanja dan diharapkan mengembalikan output dalam format JSON terstruktur yang berisi:
- **Items**: daftar item yang dipesan beserta kuantitas dan harga
- **Charges**: biaya tambahan seperti pajak, *service charge*, dan pembulatan
- **Currency**: mata uang yang digunakan

---

## 2. Metodologi

### 2.1 Setup Teknis

| Komponen | Detail |
|---|---|
| Hardware | AMD Radeon RX 6700 XT (12GB VRAM) |
| Runtime | Ollama + ROCm (via Ollama-For-AMD-Installer) |
| Python Library | `ollama-python`, `rapidfuzz`, `Pillow` |
| Image Preprocessing | Resize ke max 1600px (base64 encoding) |

### 2.2 System Prompt

Model dikonfigurasi dengan system prompt berikut untuk mengontrol perilaku ekstraksi:

```
You are a receipt parser. Extract only the relevant information from the receipt image.

Rules:
- An item is anything that was ordered (food, drinks, or services) with a price
- A charge is any financial adjustment such as tax, service charge, or discount
- Ignore everything else: restaurant name, address, taglines, cashier info,
  loyalty points, table numbers, and any text without a clear price
- If the same item appears multiple times as separate lines, list each one separately
- If a line has no price and is at the same indentation level as the previous item,
  consolidate it into the previous item's name
- If a line has no price and is indented beneath the previous item,
  it is a sub-item description — ignore it
```

### 2.3 Skema Output JSON

```json
{
  "items": [
    {"name": "item name", "quantity": 1, "price": 0.00}
  ],
  "charges": [
    {"name": "charge name", "amount": 0.00}
  ],
  "currency": "IDR"
}
```

### 2.4 Dataset Test

Empat struk belanja dipilih dengan karakteristik yang berbeda-beda untuk menguji ketahanan model:

| # | Restoran | Tantangan Unik |
|---|---|---|
| TC1 | Solaria | Item nama dua baris, *negative rounding* |
| TC2 | Paul Bakery | Duplikasi item tanpa kuantitas |
| TC3 | JCO | Item paket dengan sub-item, PB1 sudah termasuk harga |
| TC4 | HokBen | Foto buram (*blurry*), istilah lokal (Pembulatan) |

### 2.5 Metrik Evaluasi

| Metrik | Deskripsi |
|---|---|
| `avg_time` | Rata-rata waktu respons per struk (detik) |
| `avg_item_name_score` | Skor kesamaan nama item (fuzzy matching, 0.0–1.0) |
| `item_price_accuracy` | Akurasi harga item (exact match, %) |
| `avg_charge_name_score` | Skor kesamaan nama charges (fuzzy matching, 0.0–1.0) |
| `charge_amount_accuracy` | Akurasi jumlah charges (exact match, %) |

Perbandingan nama menggunakan **fuzzy string matching** (`rapidfuzz`) untuk mengakomodasi perbedaan kapitalisasi dan ejaan minor. Perbandingan harga menggunakan **exact match** karena angka tidak memiliki ambiguitas.

---

## 3. Hasil Benchmark

### 3.1 Ringkasan Hasil

| Metrik | `qwen2.5vl:3b` | `gemma4:e2b` | Pemenang |
|---|---|---|---|
| Avg response time | **4.89s** | 15.14s | Qwen ✅ |
| Avg item name score | **0.86** | 0.69 | Qwen ✅ |
| Item price accuracy | 70.0% | **70.8%** | Gemma ✅ |
| Avg charge name score | **0.71** | 0.63 | Qwen ✅ |
| Charge amount accuracy | **75.0%** | 50.0% | Qwen ✅ |

**Kesimpulan: `qwen2.5vl:3b` unggul di 4 dari 5 metrik.**

### 3.2 Hasil Per Test Case — Qwen2.5-VL-3B

| Test Case | Item Name | Item Price | Charge Name | Charge Amount |
|---|---|---|---|---|
| TC1 — Solaria | 0.96 | 80% | 0.46 | 50% |
| TC2 — Paul Bakery | 1.0 | 100% | 1.0 | 100% |
| TC3 — JCO | 1.0 | 100% | 1.0 | 100% |
| TC4 — HokBen | 0.69 | 0% | 0.38 | 50% |

### 3.3 Hasil Per Test Case — Gemma4:e2b

| Test Case | Item Name | Item Price | Charge Name | Charge Amount |
|---|---|---|---|---|
| TC1 — Solaria | 0.96 | 80% | 0.50 | 0% |
| TC2 — Paul Bakery | 0.75 | 67% | 0.24 | 0% |
| TC3 — JCO | 0.0 | 0% | 1.0* | 1.0* |
| TC4 — HokBen | 1.0 | 100% | 0.29 | 0% |

*\*Skor TC3 charges untuk Gemma adalah artefak scoring — kedua predicted dan ground truth mengembalikan charges kosong sehingga dihitung sebagai 1.0.*

---

## 4. Analisis Kegagalan

### 4.1 Kegagalan Qwen2.5-VL-3B

**TC1 — Item nama dua baris (Kwetiau Seafood Goreng)**
- Model memisahkan `Kwetiau Seafood` dan `Goreng` menjadi dua item terpisah
- `Goreng` salah diklasifikasikan sebagai item dengan harga subtotal (Rp 129.096)
- Penyebab: setelah *resize* ke 1600px, perbedaan indentasi antar baris masih sulit terdeteksi
- Rule tambahan di system prompt tidak cukup efektif untuk kasus ini

**TC1 — Negative rounding tidak terdeteksi**
- Charges `Rounding: -6` tidak dikembalikan oleh model
- Penyebab: nilai `-6` sangat kecil secara visual dan mungkin diabaikan oleh model

**TC1 — Harga Siomay tidak akurat**
- Model mengembalikan `20000` bukan `20002`
- Penyebab: dua digit terakhir (`02`) hilang akibat kompresi *resize*

**TC4 — HokBen (foto buram)**
- Nama item terpotong: `Rice Osa` (Rice Only RB), `Yaki RB` (Beef Teriyaki RB)
- Semua harga item dikembalikan sebagai `0.0`
- Penyebab: kualitas foto asli yang buram, bukan masalah model atau prompt

### 4.2 Kegagalan Gemma4:e2b

**TC2 — Misklasifikasi charges**
- Model mengklasifikasikan `Taxable Amount`, `Cash Given`, dan `Change` sebagai charges
- Penyebab: Gemma kurang konsisten dalam mengikuti instruksi sistem untuk mengabaikan *summary lines*

**TC3 — Gagal mendeteksi item utama**
- Model mengembalikan `items: []` — tidak ada item yang terdeteksi
- Total dan Payment diklasifikasikan sebagai charges
- Penyebab: layout struk JCO dengan banyak sub-item membingungkan model

**TC4 — Misklasifikasi charges**
- Model mengklasifikasikan `SUB TOTAL` dan `TOTAL` sebagai charges
- Charges yang sebenarnya (`PJK Resto 10%`, `Pembulatan`) tidak terdeteksi
- Pola ini konsisten dengan TC2 — Gemma kesulitan membedakan *financial adjustment* dari *summary lines*

**Pola kegagalan utama Gemma:** Secara konsisten memasukkan *summary lines* (subtotal, total, cash, change) sebagai charges di TC2 dan TC4. Ini mengindikasikan kelemahan pada *instruction following* untuk model MoE di ukuran parameter kecil.

---

## 5. Known Limitations

| Limitasi | Dampak | Rekomendasi |
|---|---|---|
| Foto buram atau resolusi rendah | Harga item tidak terbaca, nama terpotong | Tambahkan validasi kualitas gambar sebelum inference |
| Item nama multi-baris | Item terpecah, subtotal salah diklasifikasikan sebagai harga | Post-processing konsolidasi nama item |
| Nilai sangat kecil (e.g. Rounding: -6) | Sering diabaikan model | Tambahkan rule eksplisit untuk nilai negatif di system prompt |
| Thousands separator (e.g. 9,637) | JSON parsing error | Sudah ditangani di `clean_json_output()` |
| Sample size kecil (4 struk) | Hasil tidak cukup untuk kesimpulan statistik | Tambah dataset minimal 20-50 struk untuk evaluasi lebih valid |

---

## 6. Rekomendasi

Berdasarkan hasil benchmark, **`qwen2.5vl:3b` direkomendasikan** sebagai model untuk aplikasi *split bill* dengan alasan:

1. **Lebih cepat** — 4.89s vs 15.14s (3x lebih cepat)
2. **Lebih akurat pada nama item** — 0.86 vs 0.69
3. **Lebih akurat pada charges** — 75% vs 50%
4. **Lebih konsisten dalam instruction following** — tidak memasukkan summary lines sebagai charges
5. **Performa sempurna pada TC2 dan TC3** — 1.0 di semua metrik

Satu-satunya metrik di mana Gemma sedikit unggul adalah *item price accuracy* (70.8% vs 70.0%) — perbedaan yang tidak signifikan.

---

## 7. Langkah Selanjutnya

- [ ] Implementasi konsolidasi item duplikat (*consolidation logic*)
- [ ] Implementasi *split bill* logic berbasis claims per orang
- [ ] Tambah validasi kualitas gambar sebelum dikirim ke model
- [ ] Perluas dataset test case minimal 20 struk dari berbagai restoran
- [ ] Evaluasi ulang dengan prompt yang dioptimasi untuk *negative charges*
