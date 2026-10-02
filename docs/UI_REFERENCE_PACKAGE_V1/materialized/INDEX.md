# Prompt Action — Materialized UI Reference Index

Status: **BASELINE UI V1 — SOURCE OF TRUTH UNTUK SOL**

Folder ini adalah referensi yang harus dipakai untuk implementasi UI. File `.b64`, folder `package/`, dan workflow decode di luar folder ini hanya mekanisme bootstrap/recovery lama dan **bukan** referensi visual utama.

## 5 layar UI resmi

1. [01-Dashboard.jpg](images/01-Dashboard.jpg) — Dashboard / ringkasan kondisi Prompt Action.
2. [02-Sejarah-Sistem.jpg](images/02-Sejarah-Sistem.jpg) — pohon System + Snapshot.
3. [03-Per-Prompt.jpg](images/03-Per-Prompt.jpg) — pohon revision per Prompt + detail perubahan.
4. [04-Backup-Recovery.jpg](images/04-Backup-Recovery.jpg) — status recovery, backup, SHA256, dan riwayat backup.
5. [05-Pengaturan.jpg](images/05-Pengaturan.jpg) — folder, backup policy, GitHub, dan tampilan.

## Dokumen resmi

- [Spesifikasi-Lengkap-UI-Versioning-Prompt-Action-V1.docx](Spesifikasi-Lengkap-UI-Versioning-Prompt-Action-V1.docx)
- [Aturan-Resmi-Versioning-Prompt-Action-V1.docx](Aturan-Resmi-Versioning-Prompt-Action-V1.docx)
- [ASTRA_MASTER_PLAN.md](ASTRA_MASTER_PLAN.md)
- [VERSIONING_RULES.md](VERSIONING_RULES.md)
- [GPT_IMAGE_PROMPTS.md](GPT_IMAGE_PROMPTS.md)

## Aturan implementasi

- Sol wajib menjadikan kelima gambar sebagai MASTER VISUAL REFERENCE.
- Jangan redesign tanpa keputusan produk baru.
- Warna utama: putih + biru; profesional, ringan, nyaman dilihat.
- Data version tree tidak boleh hardcoded; harus berasal dari data/version history.
- Versioning resmi: `System V` + `Snapshot S` + `Prompt Revision R`.
- `Legacy V22.5.1` hanya sumber awal; baseline produk dimulai dari `System V1`.
- Nama release mengikuti `PRIMARY CHANGE`; prompt lain yang ikut menyesuaikan dicatat sebagai `SYNC CHANGE` dan revision-nya naik hanya jika isi aktual berubah.
- Setiap release resmi belum COMPLETE sebelum Full Backup + SHA256 + verifikasi tersedia.

## Catatan kualitas aset

File di folder `materialized/` adalah baseline repository yang dapat dibuka langsung dari GitHub. Jika tersedia reference image resolusi lebih tinggi di backup lokal, resolusi boleh ditingkatkan tanpa mengubah komposisi/layout/design language yang sudah dikunci.
