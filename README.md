# Bank XYZ — Customer Experience Intelligence Dashboard

Dashboard Streamlit untuk analisis kepuasan nasabah Bank XYZ.

## Struktur Folder (Flat)

```
bankxyz_dashboard/
├── app.py                              ← Entry point utama
├── requirements.txt
├── load_data.py
├── filters.py
├── theme.py
├── kpi_bar.py
├── indonesia.geojson                   ← Batas wilayah provinsi untuk peta
├── Deka_project_dataset_BankXYZ.xlsx   ← Dataset mentah (label atribut)
├── data_clean.pkl
└── data_final.pkl
```

Semua file ada di satu folder root — tidak ada subfolder `utils/`, `data/`, atau `static/`.

## Urutan Tab

| # | Tab | Isi |
|---|-----|-----|
| 1 | **Scorecard** | 5 KPI cards (Total Responden, NPS, Kepuasan Overall, Service Failure, **CES**) → Peta Provinsi → Kepuasan per Dimensi (Fisik Bank‑Brand Image‑Teller‑CS‑ATM‑Sekuriti) + Distribusi NPS → Distribusi Kepuasan & Loyalitas → Prioritas Perhatian |
| 2 | **Customer Service Index** | 4 KPI cards (Total Responden, Atribut Prioritas, Dimensi Terkritis, Gap Terbesar) → IPA filter dimensi + kuadran counter → Chart IPA → Atribut Prioritas Utama |
| 3 | **Loyalitas Index** | Segmentasi Loyalitas |
| 4 | **Profil Cabang** | Top/Bottom 5 → Radar DNA → Waktu Tunggu |
| 5 | **Peta Emosi & Profil Nasabah** | Peringatan Kualitas Data → Peta Emosi (XYZ vs Kompetitor, Korelasi NPS, Profil Emosi) → Profil Nasabah |
| 6 | **Intelijen Kompetitor** | Radar + Gap → Distribusi Bank → NPS Comparison |

## Setup Lokal

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy ke Streamlit Cloud

1. Push **semua file** ke GitHub repo (pastikan `.pkl`, `.xlsx`, dan `.geojson` ikut
   di-push — jangan dikecualikan lewat `.gitignore`)
2. Buka [share.streamlit.io](https://share.streamlit.io)
3. New app → pilih repo → **Main file path: `app.py`**
4. Deploy!

Tidak ada dependensi ke Google Drive — semua data dibaca langsung dari folder repo.

## Catatan Penting: Temuan Kualitas Data

Saat memvalidasi ulang dashboard ini terhadap data asli, ditemukan **pola straight-lining**
pada item-item emosi nasabah (`T_H1A_*`):

- **1.062 dari 1.730 responden (61,4%)** memberi skor **identik pada seluruh 15 item emosi**,
  termasuk pasangan emosi yang seharusnya berlawanan makna (misalnya "Senang" dan "Marah"
  sama-sama bernilai 6). Ini indikasi kuat responden mengisi survei tanpa membaca pertanyaan.
- Provinsi dengan proporsi straight-liner tertinggi: Jawa Barat, Banten, dan DKI Jakarta
  (secara absolut terbanyak karena jumlah respondennya besar), serta Kalimantan Selatan dan
  Sumatera Selatan secara proporsional (n=27 masing-masing).
- Dashboard sekarang menampilkan **peringatan kualitas data otomatis** di tab "Peta Emosi &
  Profil Nasabah" yang menghitung dan memvisualisasikan temuan ini secara langsung dari data
  terfilter, supaya tidak disalahartikan sebagai nilai emosi yang valid.
- **Rekomendasi**: keluarkan responden straight-liner dari analisis emosi, atau tambahkan
  pertanyaan kontrol (*attention check*) pada survei berikutnya.

## Peta Provinsi — Keterbatasan Batas Wilayah

`indonesia.geojson` yang digunakan berisi batas administratif lama (32 provinsi) dan belum
memisahkan provinsi hasil pemekaran. Akibatnya:

- **Kepulauan Riau** ditampilkan tergabung dengan **Riau** pada peta (jumlah responden
  digabung), karena pemisahan resmi Kepulauan Riau dari Riau (2004) belum tercermin di batas
  wilayah ini.
- Dashboard menampilkan catatan otomatis di bawah peta apabila ada provinsi yang
  digabungkan seperti ini, supaya transparan ke pengguna.

## Perubahan dari Versi Sebelumnya

- ✅ Struktur dikembalikan flat (semua file satu folder) sesuai permintaan, dengan seluruh
  import dan path file disesuaikan kembali
- ✅ `indonesia.geojson` ditambahkan dan peta provinsi diperbaiki agar benar-benar merender
  (skema properti sebelumnya tidak pernah cocok dengan data manapun)
- ✅ Label atribut pada "Prioritas Perhatian" dan "Atribut Prioritas Utama" ditampilkan **utuh**
  (sebelumnya terpotong tengah kalimat akibat `[:70]`)
- ✅ **Peringatan kualitas data (straight-lining)** ditambahkan di tab Peta Emosi & Profil
  Nasabah, lengkap dengan rincian per provinsi
- ✅ KPI card, header, dan sidebar dipoles dengan badge ikon dan aksen yang lebih konsisten
  bernuansa perbankan — **palet warna tidak diubah**
- ✅ Urutan tab: Scorecard → Customer Service Index → Loyalitas → Profil Cabang →
  Peta Emosi & Profil Nasabah → Intelijen Kompetitor
- ✅ **Customer Effort Score (CES)** pada KPI Scorecard (dari kolom T_J1 — kemudahan layanan
  cabang, skala 1–6) serta Service Failure sebagai KPI card
- ✅ Urutan dimensi diseragamkan: Fisik Bank → Brand Image → Teller → CS → ATM → Sekuriti
