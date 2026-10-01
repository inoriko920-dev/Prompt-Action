# Prompt Action — UI Reference Package V1

Paket ini menyimpan seluruh baseline UI Prompt Action V1 dalam bentuk potongan Base64 agar file biner tetap dapat dipulihkan dari GitHub.

Isi ZIP setelah direkonstruksi:
- `images/01-Dashboard.jpg`
- `images/02-Sejarah-Sistem.jpg`
- `images/03-Per-Prompt.jpg`
- `images/04-Backup-Recovery.jpg`
- `images/05-Pengaturan.jpg`
- `docs/Spesifikasi-UI-Versioning-Prompt-Action-V1.docx`
- `docs/Aturan-Resmi-Versioning-Prompt-Action-V1.docx`

SHA256 ZIP:
`514a01befbfe50946431b82aa0bcf03415fa36460976b1db2091da65024a7799`

## Restore di Windows PowerShell
Jalankan `rebuild-ui-reference.ps1` dari folder ini. Script akan menggabungkan semua `part-*.b64`, membuat kembali ZIP, dan memeriksa SHA256.

Lima gambar adalah **MASTER VISUAL REFERENCE** untuk implementasi Sol. Jangan redesign tanpa keputusan produk baru.
