# Prompt Action — ASTRA MASTER PLAN V1

Status: **PLANNED / SOURCE OF TRUTH UNTUK SOL**  
Peran pemilik plan: **ASTRA**  
Tanggal baseline: **1 Oktober 2026**

> Dokumen ini menggantikan plan lama yang masih memakai versi V22.5.2 sebagai versi aktif. Mulai sekarang V22.5.1 hanya `LEGACY SOURCE`; Prompt Action dimulai ulang sebagai `SYSTEM V1`.

---

## 1. Tujuan produk

Prompt Action adalah aplikasi desktop Windows untuk:

- melihat sejarah sistem dan perubahan prompt secara visual;
- melihat revisi setiap Prompt tanpa membaca spreadsheet teknis;
- mengetahui `PRIMARY CHANGE` dan prompt lain yang hanya ikut menyesuaikan (`SYNC CHANGE`);
- mengunduh prompt aktif maupun revisi lama yang benar-benar tersedia;
- membandingkan revisi;
- membuat dan memverifikasi Full Backup;
- membangun ulang repository bila GitHub hilang atau akun suspend.

Aplikasi V1 adalah **Version Manager + Prompt Library + Backup/Recovery Manager**, bukan editor prompt panjang.

---

## 2. Aturan versioning resmi

Gunakan tiga lapis identitas. Jangan gunakan angka seperti `1.1.1.1.1`.

### 2.1 System Version — `V`

Contoh: `V1`, `V2`, `V3`.

Naik hanya jika arsitektur/workflow global berubah secara material. Perubahan satu prompt tidak membuat System Version baru.

Titik awal:

```text
Legacy V22.5.1
      │
      ▼
System V1
```

### 2.2 Snapshot — `S`

Contoh: `S001`, `S002`, `S003`.

Snapshot naik setiap release resmi pada System Version yang sama.

Contoh:

```text
SYSTEM V1
  ├─ S001  Baseline
  ├─ S002  Update Prompt 3
  ├─ S003  Update Prompt 2
  └─ S004  Update Prompt 3
```

### 2.3 Prompt Revision — `R`

Contoh: `R1`, `R2`, `R3`.

Revision naik pada setiap file prompt yang **isi aktualnya berubah**.

Contoh keadaan sistem:

```text
Prompt 1A   R1
Prompt 1B   R1
Prompt 1B1  R1
Prompt 1B2  R3
Prompt 2    R2
Prompt 3    R3
Prompt 4    R3
Prompt 5    R2
```

### 2.4 PRIMARY CHANGE vs SYNC CHANGE

Nama update mengikuti `PRIMARY CHANGE`, sedangkan nomor revision mengikuti semua file yang isinya benar-benar berubah.

Contoh:

```text
S002 — Update Prompt 3

PRIMARY
Prompt 3      R1 → R2

SYNC
Prompt 1B2    R1 → R2
Prompt 4      R1 → R2
Prompt 5      R1 → R2
```

Release tetap disebut **Update Prompt 3** karena Prompt 3 adalah alasan utama perubahan. Prompt 1B2/4/5 hanyalah penyesuaian kompatibilitas, tetapi revision mereka tetap naik karena isi file berubah.

Jika nanti hanya Prompt 2 berubah:

```text
S003 — Update Prompt 2
PRIMARY: Prompt 2 R1 → R2
```

Prompt lain mempertahankan revision sebelumnya apabila kontennya tidak berubah.

### 2.5 Kapan V1 menjadi V2

Hanya jika struktur sistem berubah besar, misalnya:

- alur 1B → 1B1 → 1B2 → Prompt 2 → Prompt 3 → Prompt 4 → Prompt 5 berubah;
- peran Jangkar/Narasi berubah total;
- format output global berubah;
- model ownership visual berubah;
- hampir seluruh prompt harus beradaptasi secara struktural.

Saat itu buat `SYSTEM V2 / S001` dan jadikan V1 arsip utuh.

---

## 3. Aturan release dan backup

Snapshot resmi **belum COMPLETE** sampai seluruh backup selesai.

Urutan wajib:

1. tentukan `PRIMARY CHANGE`;
2. identifikasi `SYNC CHANGE`;
3. arsipkan revision lama;
4. simpan revision baru;
5. update metadata/version history;
6. buat Snapshot baru dengan status `BACKUP REQUIRED`;
7. buat Full Backup ZIP;
8. buat SHA256;
9. verifikasi ZIP;
10. simpan salinan kedua;
11. baru ubah status Snapshot menjadi `COMPLETE`.

Aturan mutlak:

> **Perubahan belum dianggap selesai sebelum Full Backup + SHA256 + verifikasi dibuat.**

GitHub bukan satu-satunya backup.

---

## 4. Arsitektur aplikasi

Target: Windows 11, portable multi-file ZIP.

Rekomendasi implementasi:

- **PySide6 + Qt Quick/QML** untuk UI;
- Python backend untuk version/file/backup/recovery operations;
- QML hanya presentation layer;
- data tree/status harus berasal dari JSON lokal, bukan hardcoded;
- tidak membutuhkan server/cloud untuk operasi inti;
- portable folder multi-file, bukan single EXE.

Sumber data canonical, misalnya:

```text
data/
  version_history.json
  settings.json
```

Model minimal:

```json
{
  "active_system": "V1",
  "active_snapshot": "S004",
  "systems": [],
  "snapshots": [],
  "prompts": {},
  "backups": [],
  "release_policy": {}
}
```

---

## 5. MASTER DESIGN LOCK

Semua layar harus terlihat sebagai aplikasi yang sama.

### Karakter visual

- perpaduan **putih + biru**;
- sidebar biru gelap → medium;
- workspace putih / biru-abu sangat muda;
- card putih, border biru-abu tipis;
- radius sekitar 12–16 px;
- shadow sangat halus;
- heading navy gelap;
- teks sekunder abu kebiruan;
- primary action vivid blue;
- hijau hanya untuk status aman/valid;
- amber hanya untuk warning/Backup Required;
- merah hanya untuk error/destructive;
- font Segoe UI / Segoe UI Variable / Inter-like;
- nyaman dibaca lama, tidak padat.

### Layout global

Sidebar kiri selalu berisi:

1. Prompt Action;
2. subtitle `Kelola prompt, versi, dan backup dengan jelas.`;
3. Dashboard;
4. Sejarah Sistem;
5. Per Prompt;
6. Backup;
7. Pengaturan;
8. status bawah `Siap bekerja`.

Topbar **tidak memakai avatar dan notification bell**.

Topbar berisi:

```text
[Judul + subtitle]        [Cari...]   System V1 • S004   ● Backup Aman
```

Reference viewport utama: sekitar **1672 × 941** (16:9).

---

## 6. SCREEN 01 — DASHBOARD

Tujuan: menjawab `Sekarang kondisi Prompt Action bagaimana?`

Header:

- Dashboard;
- `Ringkasan kondisi Prompt Action`.

KPI:

- System Aktif — V1;
- Snapshot Aktif — S004;
- Prompt Aktif — 8;
- Backup — AMAN.

Card `Perubahan Terakhir`:

```text
S004 — Update Prompt 3
PRIMARY CHANGE
Prompt 3 R2 → R3

SYNC CHANGE
Prompt 1B2 R2 → R3
Prompt 4   R2 → R3
```

Tombol:

- Lihat Snapshot;
- Buka Prompt Aktif;
- Lihat Perubahan Terakhir;
- Download Full Backup;
- Buka Backup;
- Buat Backup Sekarang.

Card `Prompt Aktif` menampilkan delapan prompt beserta revision aktif.

Card `Status Backup` menampilkan:

- Full Backup;
- SHA256;
- Verifikasi ZIP;
- Salinan Kedua;
- Recovery: AMAN / BELUM AMAN.

---

## 7. SCREEN 02 — SEJARAH SISTEM

Header:

- Sejarah Sistem;
- `System, snapshot, dan kesinambungan perubahan`.

Pohon utama:

```text
Legacy V22.5.1  →  System V1
                       │
                       ├─ S001 Baseline
                       ├─ S002 Update Prompt 3
                       ├─ S003 Update Prompt 2
                       └─ S004 Update Prompt 3  ← aktif
```

Jangan tampilkan V21.5/V22.x sebagai cabang utama. Detail sejarah lama boleh tetap ada sebagai arsip metadata, tetapi UI utama dimulai dari satu node `Legacy V22.5.1`.

Panel `Detail Snapshot`:

- System;
- Snapshot;
- Status;
- Primary Change;
- Sync Change;
- Backup;
- alasan perubahan.

Tombol:

- Buka Detail;
- Lihat Prompt yang Berubah;
- Download Snapshot Backup;
- Bandingkan dengan snapshot sebelumnya;
- Lihat Changelog.

---

## 8. SCREEN 03 — PER PROMPT

Ini halaman utama untuk penggunaan sehari-hari.

Header contoh:

```text
Prompt 3
Eksekusi Langsung Satu Narasi
System V1 • Revision Aktif R3
```

Selector atas:

- Prompt 1A;
- Prompt 1B;
- Prompt 1B1;
- Prompt 1B2;
- Prompt 2;
- Prompt 3;
- Prompt 4;
- Prompt 5.

`Pohon Revision` contoh:

```text
R1 ───→ R2 ───→ R3
         │        AKTIF
         └── Draft A (Eksperimen)
```

Draft tidak masuk mainline resmi sampai dipromosikan menjadi release.

Panel `Detail Revision`:

- Revision;
- Parent;
- Snapshot;
- Status;
- Primary Change;
- Apa yang berubah?;
- Menyesuaikan / sync impacts.

Contoh ringkasan Prompt 3:

- verifikasi 1B2 ke MP4 per frasa;
- moving visual maksimal 3 detik final;
- slow 0,50× tetap;
- ambil-lewati ±50% per frasa;
- freeze maksimal 5 detik;
- acak menjadi tahap paling terakhir.

Card `File Tersedia`:

- Download Prompt Aktif;
- Download Revision Ini;
- Bandingkan R2 vs R3;
- Lihat Snapshot;
- Buka Changelog;
- Tambah Revisi.

UI ini **bukan text editor**. Jangan tampilkan textarea besar berisi seluruh prompt.

---

## 9. SCREEN 04 — BACKUP & RECOVERY

Header:

- Backup & Recovery;
- `Pastikan Prompt Action dapat dibangun ulang kapan pun`.

Status besar:

```text
STATUS PEMULIHAN
AMAN
Snapshot S004 sudah memiliki backup terverifikasi.
```

Checklist `Kelengkapan Recovery`:

- Prompt aktif tersimpan;
- Revision lama tersimpan;
- VERSION_DATA tersimpan;
- Changelog tersimpan;
- Full Backup ZIP;
- SHA256;
- ZIP terverifikasi;
- Salinan kedua.

Card `Backup Terbaru`:

- nama ZIP;
- System;
- Snapshot;
- tanggal;
- ukuran;
- SHA256 VALID;
- verify PASS;
- second copy tersedia.

Tombol:

- Download Full Backup;
- Download SHA256;
- Verifikasi Backup;
- Buka Recovery Guide;
- Buka Folder Backup;
- Buat Backup Baru.

Riwayat Backup menampilkan S001, S002, S003, S004 beserta status VALID/FAILED/REQUIRED.

---

## 10. SCREEN 05 — PENGATURAN

Bagian `Umum`:

- Folder Root Prompt Action;
- Folder Prompt;
- Folder Backup;
- tombol Pilih Folder;
- indikator Valid/Invalid.

Bagian `Backup`:

- Buat backup setiap release;
- Buat SHA256;
- Verifikasi ZIP setelah dibuat;
- Simpan salinan kedua;
- Second Copy Location.

Bagian `GitHub`:

- Repository `inoriko920-dev/Prompt-Action`;
- Branch `main`;
- Status Terhubung;
- Buka Repository;
- Tes Koneksi;
- catatan `GitHub bukan satu-satunya backup.`

Bagian `Tampilan`:

- Theme = `Light — Prompt Action Blue`;
- UI Scale = 100%;
- Tree Density = Comfortable.

Advanced:

- Buka Log;
- Reset Layout;
- Export Diagnostics.

Footer:

- Batal;
- Simpan Pengaturan.

---

## 11. Dialog / modal minimum

Implementasikan state berikut dengan design system yang sama:

- Tambah Revisi / Release Prompt;
- Detail Version/Snapshot;
- Compare Revision;
- Backup Progress;
- Backup Success;
- Backup Failed;
- Restore Backup;
- Delete Draft confirmation;
- GitHub Connection Error;
- empty state;
- loading state;
- disabled state + alasan.

Contoh `Tambah Revisi`:

```text
Prompt: Prompt 3
Revision sekarang: R2
Revision baru: R3
Primary Change: Prompt 3
Affected Prompt:
  [x] Prompt 1B2
  [x] Prompt 4
  [ ] Prompt 5
Ringkasan perubahan: ...
Alasan: ...
[Batal] [Lanjutkan]
```

Setelah release dibuat, Snapshot berstatus `BACKUP REQUIRED`; hanya berubah menjadi `COMPLETE` setelah workflow backup lolos.

---

## 12. Search

Search awal dapat mencari:

- nama Prompt;
- Revision;
- Snapshot;
- ringkasan perubahan;
- alasan perubahan.

Full-text seluruh isi TXT tidak wajib pada implementasi pertama.

---

## 13. File/folder target

```text
Prompt-Action/
├─ app/
├─ data/
│  ├─ version_history.json
│  └─ settings.json
├─ prompts/
│  ├─ V1/
│  │  ├─ Prompt-1A/
│  │  ├─ Prompt-1B/
│  │  ├─ Prompt-1B1/
│  │  ├─ Prompt-1B2/
│  │  ├─ Prompt-2/
│  │  ├─ Prompt-3/
│  │  ├─ Prompt-4/
│  │  └─ Prompt-5/
│  └─ legacy/V22.5.1/
├─ backups/
├─ docs/
└─ scripts/
```

Nama prompt release:

```text
Prompt-3_V1_R1.txt
Prompt-3_V1_R2.txt
Prompt-2_V1_R1.txt
Prompt-2_V1_R2.txt
```

Snapshot tidak wajib masuk ke nama file prompt karena Snapshot adalah keadaan seluruh sistem.

---

## 14. Reference UI resmi

Folder repo:

```text
docs/UI_REFERENCE_PACKAGE_V1/
```

Reference screens yang wajib diikuti:

1. Dashboard;
2. Sejarah Sistem;
3. Per Prompt;
4. Backup & Recovery;
5. Pengaturan.

Jika ada konflik antara improvisasi implementer dan reference image, **reference image + MASTER DESIGN LOCK menang** selama tidak merusak fungsi.

---

## 15. Fase implementasi SOL

### UI-001 — Repo/data foundation
- struktur app/data/prompts/backups/docs/scripts;
- schema JSON;
- model V/S/R;
- dummy data S001–S004.

### UI-002 — Shell pixel-match
- Windows shell;
- sidebar;
- topbar;
- typography;
- card/button/toggle/input tokens.

### UI-003 — Dashboard
- KPI;
- perubahan terakhir;
- prompt aktif;
- backup health.

### UI-004 — Sejarah Sistem
- System Tree;
- Snapshot Tree;
- detail selection.

### UI-005 — Per Prompt
- selector Prompt;
- Revision Tree;
- Draft branch;
- Detail Revision;
- File Tersedia.

### UI-006 — Backup & Recovery
- Full Backup;
- SHA256;
- verify;
- second-copy status;
- history.

### UI-007 — Pengaturan
- folder settings;
- backup policies;
- GitHub info;
- UI scale/density.

### UI-008 — Dialog/state
- release wizard;
- compare;
- loading/success/error/disabled;
- restore.

### UI-009 — Visual parity pass
Ambil screenshot aplikasi nyata pada viewport reference dan bandingkan dengan lima gambar referensi. Perbaiki spacing, font size, radius, border, alignment, density, dan hierarchy sebelum UI dianggap selesai.

### UI-010 — Portable smoke test
- build onedir;
- ZIP portable;
- extract pada folder baru;
- launch tanpa Python manual;
- navigasi seluruh halaman;
- cek tombol minimum.

---

## 16. Acceptance criteria

UI belum dianggap selesai jika salah satu berikut gagal:

1. kelima halaman utama dapat dibuka;
2. semua halaman memakai design language yang sama;
3. tree berasal dari data terstruktur, bukan hardcoded;
4. perubahan satu Prompt tidak otomatis membuat System V baru;
5. Primary vs Sync Change terlihat jelas;
6. Snapshot belum COMPLETE sebelum backup valid;
7. setiap tombol visible mempunyai aksi nyata atau disabled reason;
8. tidak ada avatar/bell SaaS yang tidak diperlukan;
9. UI nyaman pada scaling Windows 100%, 125%, 150%;
10. portable ZIP dapat diekstrak dan dijalankan;
11. screenshot implementasi dibandingkan dengan reference UI;
12. tidak ada token/API key/cookie pribadi di repo/log/backup.

---

## 17. Handoff ASTRA → SOL

SOL harus menganggap dokumen ini sebagai plan utama. Jangan mengubah keputusan arsitektur/versioning/design lock tanpa alasan teknis yang jelas.

Urutan prioritas:

1. data/versioning benar;
2. shell UI semirip mungkin dengan reference;
3. lima screen utama selesai;
4. release + backup workflow aman;
5. portable package;
6. visual parity pass.

Jika implementasi menemukan konflik teknis yang memerlukan perubahan arsitektur, hentikan bagian tersebut dan dokumentasikan masalah untuk review ASTRA; jangan diam-diam mengganti model V/S/R atau design language.
