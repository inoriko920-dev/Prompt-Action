# Prompt Action — 5 Official GPT Image Prompts

Status: **MASTER VISUAL PROMPT V1**  
System: **V1**  
Baseline visual: putih + biru, professional, calm, desktop Windows.

## MASTER DESIGN LOCK — wajib dipakai pada semua gambar

Create a high-fidelity desktop Windows application UI mockup for an app named **"Prompt Action"**. The design language MUST remain identical across all screens in this series. Use a premium professional white-and-blue productivity style: a deep-to-medium blue vertical sidebar, white main workspace, very pale blue-gray page background, white cards with subtle 1px blue-gray borders, 12–16px rounded corners, minimal soft shadows, navy primary text, muted blue-gray secondary text, vivid blue only for primary actions, selected navigation, active version nodes, and focus states. Use green only for validated/safe status, amber for attention/backup required, and red only for failures/destructive warnings. Typography should resemble Segoe UI/Inter: clean, compact, highly readable, comfortable for long use. Maintain an 8px spacing rhythm, generous whitespace, balanced card density, consistent outline icons, 40–44px buttons, and a calm enterprise-grade feel.

The application window should be 16:9 desktop, approximately 1600x900 visual composition. Keep the same sidebar width, same top header height, same typography scale, same icon family, same radii, same button styles, same blue gradient, and same card visual language on every screen.

The left sidebar always shows: **Prompt Action**, subtitle **"Kelola prompt, versi, dan backup dengan jelas."**, then **Dashboard**, **Sejarah Sistem**, **Per Prompt**, **Backup**, **Pengaturan**. Highlight only the current page. At the bottom show a compact local status card **"Siap bekerja"** with a small green dot when healthy.

The topbar must NOT show an avatar or notification bell. Instead show page title/subtitle on the left, a search field near the right, then **"System V1 • S004"** and a compact backup health indicator **"Backup Aman"** with a small green dot. Avoid SaaS account/profile visual patterns.

Treat this as a real implemented desktop product, not a conceptual infographic. All controls must look clickable and aligned. Indonesian UI text must be sharp and legible. Do not use external brand logos. Do not add decorative charts unrelated to the specified workflow.

---

## 01 — Dashboard

SCREEN 01 — DASHBOARD. Highlight **Dashboard** in the sidebar. Page title: **Dashboard**. Subtitle: **Ringkasan kondisi Prompt Action**.

Create a KPI row with four clean cards: **System Aktif — V1**, **Snapshot Aktif — S004**, **Prompt Aktif — 8**, and **Backup — AMAN** with a small green validated badge.

Below, create a large card titled **Perubahan Terakhir** showing **S004 — Update Prompt 3**. Clearly separate **PRIMARY CHANGE** and **SYNC CHANGE**. Primary: **Prompt 3 R2 → R3**. Sync: **Prompt 1B2 R2 → R3** and **Prompt 4 R2 → R3**. Include a blue secondary button **Lihat Snapshot**.

Create a section **Prompt Aktif** with eight compact cards: Prompt 1A R1, Prompt 1B R1, Prompt 1B1 R1, Prompt 1B2 R3, Prompt 2 R2, Prompt 3 R3, Prompt 4 R3, Prompt 5 R2. Prompt 3 may have a subtle active accent, but do not make the section noisy.

Create a card **Status Backup** with checklist: Full Backup ✓, SHA256 ✓, Verifikasi ZIP ✓, Salinan Kedua ✓. Show **Recovery: AMAN** in a calm green pill. Buttons: **Download Full Backup** and **Buka Backup**.

Add **Aksi Cepat**: **Buka Prompt Aktif**, **Lihat Perubahan Terakhir**, **Buat Backup Sekarang**. The page should feel spacious, calm, immediately understandable, and more like a polished desktop version manager than an analytics dashboard.

---

## 02 — Sejarah Sistem

SCREEN 02 — SEJARAH SISTEM. Highlight **Sejarah Sistem** in the sidebar. Page title: **Sejarah Sistem**. Subtitle: **System, snapshot, dan kesinambungan perubahan**.

The main hero card is titled **Pohon Sistem**. Show a clean visual lineage: a muted legacy node **Legacy V22.5.1** → a strong blue selected node **System V1**. Under System V1 display a vertical or gently branching snapshot timeline: **S001 — Baseline**, **S002 — Update Prompt 3**, **S003 — Update Prompt 2**, **S004 — Update Prompt 3**, with S004 highlighted as active. Do NOT show old V21/V22.x versions as primary branches; V22.5.1 is the only legacy source shown in the main tree.

On the right create **Detail Snapshot** for S004. Show: System V1, Snapshot S004, Status COMPLETE, Primary Change: Prompt 3 R2 → R3, Sync Change: Prompt 1B2 R2 → R3 and Prompt 4 R2 → R3, Backup: VALID. Include a short Indonesian reason paragraph.

Buttons: **Buka Detail**, **Lihat Prompt yang Berubah**, **Download Snapshot Backup**, **Bandingkan dengan S003**, **Lihat Changelog**. Include a small legend for Legacy, Snapshot, Active, Backup Valid. The tree must be elegant, not dense.

---

## 03 — Per Prompt

SCREEN 03 — PER PROMPT. Highlight **Per Prompt** in the sidebar. Page title: **Prompt 3**. Subtitle: **Eksekusi Langsung Satu Narasi**. In the header show **System V1** and **Revision Aktif R3**.

At the top create a compact selector for: Prompt 1A, Prompt 1B, Prompt 1B1, Prompt 1B2, Prompt 2, Prompt 3, Prompt 4, Prompt 5. Prompt 3 is selected in blue.

Main left card: **Pohon Revision**. Show **R1 → R2 → R3**, with R3 solid blue and labeled **AKTIF**. From R2 show an optional dashed branch **Draft A** to demonstrate experiments without making the draft part of the official mainline. Use labels under nodes such as S001, S002, S004.

Main right card: **Detail Revision**. Selected revision R3. Show Parent R2, Snapshot S004, Status Aktif, Primary Change Prompt 3, and **Apa yang berubah?**: verifikasi 1B2 ke MP4 per frasa; moving visual maksimal 3 detik final; slow 0,50× tetap; ambil-lewati ±50% per frasa; freeze maksimal 5 detik; acak menjadi tahap paling terakhir. Show sync impacts: Prompt 1B2 and Prompt 4.

Below add **File Tersedia** with buttons: **Download Prompt Aktif**, **Download Revision Ini**, **Bandingkan R2 vs R3**, **Lihat Snapshot S004**, **Buka Changelog**, **Tambah Revisi**. Add TXT filename and checksum indicator. It must NOT look like a text editor.

---

## 04 — Backup & Recovery

SCREEN 04 — BACKUP & RECOVERY. Highlight **Backup** in the sidebar. Page title: **Backup & Recovery**. Subtitle: **Pastikan Prompt Action dapat dibangun ulang kapan pun**.

Create a prominent recovery status card: **STATUS PEMULIHAN — AMAN** with green shield/check icon, plus **Snapshot S004 sudah memiliki backup terverifikasi.**

Create **Kelengkapan Recovery** with: Prompt aktif tersimpan ✓; Revision lama tersimpan ✓; VERSION_DATA tersimpan ✓; Changelog tersimpan ✓; Full Backup ZIP ✓; SHA256 ✓; ZIP terverifikasi ✓; Salinan kedua ✓.

Create **Backup Terbaru** showing **Prompt-Action-V1-S004-FULL-BACKUP.zip**, System V1, Snapshot S004, date, size, SHA256 VALID, verify PASS, second copy available. Buttons: **Download Full Backup**, **Download SHA256**, **Verifikasi Backup**, **Buka Recovery Guide**, **Buka Folder Backup**, **Buat Backup Baru**.

Create **Riwayat Backup**: S001 VALID, S002 VALID, S003 VALID, S004 VALID. At bottom include blue callout: **Perubahan belum dianggap selesai sebelum Full Backup + SHA256 + verifikasi dibuat.** Also show a small amber example state **Backup Required**.

---

## 05 — Pengaturan

SCREEN 05 — PENGATURAN. Highlight **Pengaturan** in the sidebar. Page title: **Pengaturan**. Subtitle: **Lokasi data, backup, GitHub, dan tampilan**.

Use a clean settings layout with sections: **Umum**, **Backup**, **GitHub**, **Tampilan**, **Advanced**.

UMUM: Folder Root Prompt Action, Folder Prompt, Folder Backup. Each path field has **Pilih Folder** and validation indicator.

BACKUP: enabled toggles for **Buat backup setiap release**, **Buat SHA256**, **Verifikasi ZIP setelah dibuat**, **Simpan salinan kedua**. Include Second Copy Location.

GITHUB: Repository = **inoriko920-dev/Prompt-Action**, Branch = **main**, Status = **Terhubung** with green dot. Buttons: **Buka Repository**, **Tes Koneksi**. Note: **GitHub bukan satu-satunya backup.**

TAMPILAN: Theme = **Light — Prompt Action Blue**, UI Scale = 100%, Tree Density = Comfortable. Do not emphasize dark mode.

ADVANCED: **Buka Log**, **Reset Layout**, **Export Diagnostics**.

Bottom-right: blue primary **Simpan Pengaturan** and white secondary **Batal**. The screen should look premium, uncluttered, and professionally grouped.
