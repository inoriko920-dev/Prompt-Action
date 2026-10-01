# Prompt Action — UI Reference Package V1

Status: **CANONICAL UI REFERENCE / ASTRA → SOL**  
System: **V1**  
Repository: `inoriko920-dev/Prompt-Action`

Folder ini adalah sumber resmi untuk implementasi UI Prompt Action V1.

## Yang wajib dipakai Sol

1. `../../PLAN.md` — source-of-truth Astra untuk versioning, arsitektur, workflow backup, fungsi layar, dan acceptance criteria.
2. `GPT_IMAGE_PROMPTS.md` — MASTER DESIGN LOCK + 5 prompt gambar resmi.
3. `materialized/images/` — 5 reference image yang sudah berhasil didecode dan diverifikasi oleh GitHub Actions:
   - `01-Dashboard.jpg`
   - `02-Sejarah-Sistem.jpg`
   - `03-Per-Prompt.jpg`
   - `04-Backup-Recovery.jpg`
   - `05-Pengaturan.jpg`
4. `Prompt-Action-UI-Reference-Materialized-V1.zip` — paket referensi UI resmi yang dapat diunduh.
5. `Prompt-Action-UI-Reference-Materialized-V1.zip.sha256` — checksum paket resmi.

## Aturan visual

Implementasi bukan redesign. Sol harus mengikuti reference putih + biru ini seakurat mungkin: sidebar, hierarchy, spacing, card, button, status, tree, typography, dan kepadatan layout harus konsisten antar-layar.

Jika teks contoh pada gambar berbeda dengan data runtime, **struktur/visual gambar dipertahankan tetapi data berasal dari source-of-truth JSON aplikasi**.

## Tentang folder `images/*.b64`

File `.b64` adalah sumber transport untuk keterbatasan upload biner melalui konektor. GitHub Actions mendecode sumber tersebut menjadi file JPG asli di `materialized/images/`.

Untuk implementasi dan review visual, gunakan **`materialized/images/*.jpg`**, bukan file `.b64`.

## Paket lama

`Prompt-Action-UI-Reference-Package-V1.zip` adalah artefak percobaan awal dan **BUKAN paket canonical**.

Paket canonical adalah:

`Prompt-Action-UI-Reference-Materialized-V1.zip`

## Bukti saat ini

Workflow `Materialize UI Reference Package` sudah berhasil menjalankan decode kelima reference image dan menghasilkan paket materialized + SHA256.

## Aturan selesai UI

Sol belum boleh menyatakan UI selesai hanya karena aplikasi dapat dibuka. Sebelum DONE:

- ambil screenshot aplikasi nyata untuk 5 halaman;
- bandingkan dengan 5 reference image;
- perbaiki visual parity yang material;
- uji button/state utama;
- uji skala/DPI dan ukuran window yang disyaratkan;
- build portable folder multi-file ZIP;
- ekstrak ZIP final dan jalankan aplikasi dari hasil ekstraksi.
