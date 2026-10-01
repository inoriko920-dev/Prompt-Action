# Prompt Action — ASTRA UI Plan

Status: PLANNED
Peran pemilik plan: ASTRA
Baseline repo saat plan dibuat: main @ dd58008c17637e910b461e2fbacf4212c85a2c2e
Tanggal: 2026-10-01

## 1. Tujuan produk
Membangun aplikasi desktop Windows bernama **Prompt Action** untuk melihat sejarah versi prompt secara visual, memahami perubahan, memilih versi aktif, mengunduh file prompt yang tersedia, dan mengunduh backup penuh untuk recovery bila GitHub bermasalah.

Fokus utama UI adalah **mudah dibaca oleh pemilik produk**, bukan menampilkan database teknis seperti Excel.

## 2. Keputusan desain yang dikunci

### Referensi visual resmi
Gunakan mockup biru-putih Prompt Action yang disetujui pemilik produk sebagai **source of truth visual**.

Referensi desain:
- ukuran referensi: 1672 × 941 px;
- tema: putih + biru;
- sidebar biru vertikal di kiri;
- area kerja utama putih terang;
- kartu putih dengan border tipis, radius lembut, dan shadow sangat halus;
- tampilan utama `Per Prompt`;
- hierarchy harus sama dengan mockup: header → Pohon Versi + Ringkasan Versi → tiga kartu bawah.

Sol tidak boleh mengganti gaya menjadi dashboard lain hanya karena lebih mudah diimplementasikan.

### Arsitektur UI
- Desktop Windows.
- **PySide6 + Qt Quick/QML**.
- Python menjadi backend untuk file/version/backup operations.
- QML menjadi presentation layer untuk mencapai layout modern dan konsisten.
- Data versi tidak di-hardcode di komponen UI; UI membaca satu sumber data JSON.
- Distribusi akhir: **portable folder multi-file dalam satu ZIP**, bukan installer dan bukan single-file EXE.

## 3. Struktur layar utama

### 3.1 Sidebar kiri
Lebar target pada viewport referensi: sekitar 270 px.

Elemen, dari atas ke bawah:
1. Judul `Prompt Action`.
2. Subtitle: `Kelola prompt, versi, dan perubahan dengan lebih baik.`
3. Menu:
   - Dashboard
   - Sejarah Sistem
   - Per Prompt
   - Backup
   - Pengaturan
4. `Per Prompt` aktif dengan panel biru lebih terang.
5. Status card kecil di bawah: `Siap bekerja`.

Sidebar menggunakan gradasi biru gelap → biru terang yang lembut, bukan neon.

### 3.2 Header
- icon dokumen;
- judul halaman: `Prompt 3`;
- subjudul: `Riwayat versi dan perubahan`;
- kotak pencarian di kanan;
- notification icon;
- avatar/status;
- custom titlebar Windows dengan minimize / maximize / close bila diperlukan untuk menyamai mockup.

### 3.3 Kartu `Pohon Versi`
Ini adalah fokus utama layar.

Urutan sejarah sistem yang wajib bisa ditampilkan:
`V21.5 → V22 → V22.1 → V22.2 → V22.3 → V22.4 → V22.5 → V22.5.1 → V22.5.2`

Status node:
- abu/pucat = riwayat saja / file tidak tersedia;
- biru muda = file tersedia;
- biru utama = aktif;
- garis putus-putus = draft.

Untuk Prompt 3:
- versi sejarah sebelum V22.5.1 tetap ditampilkan walaupun file fisiknya tidak tersedia;
- V22.5.1 = file tersedia;
- V22.5.2 = aktif;
- draft V22.6 dan V22.6.1 boleh tampil sebagai cabang draft, bukan sebagai rilis resmi.

Node harus bisa diklik. Saat node dipilih, panel ringkasan dan kartu perubahan diperbarui.

### 3.4 `Ringkasan Versi`
Panel kanan atas berisi:
- Versi aktif/terpilih;
- Parent;
- Status;
- Prompt;
- Deskripsi perubahan singkat.

Jangan tampilkan informasi teknis berlebihan di panel ini.

### 3.5 `Apa yang Berubah?`
Kartu kiri bawah.

Untuk V22.5.2 Prompt 3 contoh ringkasan:
- Verifikasi 1B2 ke MP4 per frasa;
- Slow 0,50× tetap;
- Ambil-lewati ±50% per frasa;
- Freeze maksimal 5 detik;
- Acak menjadi tahap terakhir.

Tujuan kartu ini adalah menjawab pertanyaan pemilik produk: **"Apa bedanya versi ini dengan versi sebelumnya?"**

### 3.6 `File Tersedia`
Kartu tengah bawah.

Tombol minimum:
- Download Prompt [versi terpilih];
- Download Full Backup terbaru;
- Lihat Changelog;
- Lihat Recovery Guide.

Jika node hanya `riwayat saja`, tombol download prompt disabled dan tampilkan `File versi ini tidak tersedia di backup`.

### 3.7 `Aturan Backup`
Kartu kanan bawah.

Checklist:
- Arsipkan versi lama;
- Simpan versi baru;
- Update changelog;
- Buat ZIP backup penuh;
- Buat SHA256;
- Simpan salinan kedua.

Footer wajib:
`Perubahan belum dianggap selesai sebelum backup dibuat.`

## 4. Sistem data agar app ikut berubah setiap ada versi baru

Buat satu file canonical, misalnya:
`data/version_history.json`

Minimal model data:
```json
{
  "system_versions": [],
  "prompts": {},
  "latest_backup": {},
  "release_policy": {}
}
```

Setiap version node minimal punya:
- `version`;
- `parent`;
- `status`: history | available | active | draft;
- `release_date`;
- `summary`;
- `changes[]`;
- `artifact_available`;
- `prompt_file`;
- `backup_file` bila relevan;
- `official_release` boolean.

UI tidak boleh diubah manual hanya karena versi baru muncul. Release process yang memperbarui JSON harus otomatis membuat pohon versi berubah.

## 5. Aturan sumber sejarah
- Riwayat lama berasal dari dokumen riwayat V22.5.1 yang sudah tersedia di backup.
- Jangan mengarang keberadaan file versi lama.
- Node versi lama boleh ada meski hanya metadata sejarah.
- Download hanya aktif untuk file fisik yang benar-benar ada.
- Rilis resmi saat ini: `Prompt 3 V22.5.2`, parent resmi `V22.5.1`.
- `Draft V22.6` dan `Draft V22.6.1` bukan parent resmi V22.5.2.

## 6. Warna dan token visual awal
Nilai di bawah adalah target awal; Sol boleh fine-tune berdasarkan screenshot comparison, bukan mengubah karakter desain.

- main background: `#F6FAFF` sampai `#FFFFFF`;
- card background: `#FFFFFF`;
- sidebar dark: sekitar `#0759B8`;
- sidebar bright: sekitar `#0C7FF2`;
- primary/action blue: sekitar `#0B7CF2`;
- active blue: sekitar `#087BF2`;
- light blue surface: sekitar `#EAF4FF`;
- dark heading: sekitar `#0B1835`;
- secondary text: sekitar `#60779B`;
- border: sekitar `#DCE9F7`;
- success: hijau lembut, hanya untuk status aktif/siap.

Typography target: Segoe UI / Segoe UI Variable di Windows, dengan ukuran dan berat mengikuti screenshot.

## 7. Perilaku UX
- Hover lembut, tidak agresif.
- Klik node menyimpan selected version sampai user memilih node lain.
- Search dapat mencari prompt, versi, atau kata kunci perubahan.
- Semua aksi download/copy harus memberi feedback sukses/gagal.
- Jangan melakukan network/background scan pada UI thread.
- App harus tetap nyaman pada scaling 100%, 125%, dan 150%.

## 8. Kriteria kesamaan UI
Reference viewport utama: **1672×941**.

Acceptance visual:
1. Struktur, posisi kelompok, rasio sidebar, ukuran kartu, spacing, radius, dan hierarchy harus sangat dekat dengan mockup.
2. Warna harus tetap putih-biru dan tidak bergeser ke tema gelap/ungu/hijau.
3. Pohon versi harus menjadi fokus visual utama.
4. Tidak boleh ada tabel Excel/data grid sebagai halaman utama.
5. Screenshot aplikasi nyata pada 1672×941 dibandingkan dengan referensi sebelum UI dinyatakan selesai.
6. Perbedaan kecil rasterisasi font/icon boleh diterima; perubahan layout, ukuran panel, warna utama, atau hierarchy tidak boleh dianggap setara.

## 9. Fase implementasi

### Fase A — Shell pixel-match
Bangun window, sidebar, header, kartu, tipografi, warna, spacing, dan titlebar. Gunakan data dummy saja. Fokus pada visual.

### Fase B — Version tree data-driven
Implementasikan version_history.json, node status, parent/branch, selection, ringkasan, dan perubahan per versi.

### Fase C — File & backup actions
Hubungkan prompt file, full backup, changelog, recovery guide, Save Copy/download lokal, dan error handling.

### Fase D — Release automation
Setiap perubahan prompt wajib:
1. arsipkan versi lama;
2. simpan versi baru;
3. update metadata/history;
4. update changelog;
5. regenerate app data;
6. buat full backup ZIP;
7. buat SHA256;
8. baru commit/push.

### Fase E — Portable build & verification
Build Windows x64 portable folder, ZIP seluruh folder, lalu uji ekstrak → run → buka versi → download/copy prompt → akses backup.

## 10. Pemicu review Astra
Minta review Astra sebelum melanjutkan bila:
- Sol ingin mengganti stack QML ke framework lain;
- layout utama harus berbeda dari mockup;
- model data versi tidak mampu mewakili cabang/draft/history-only;
- release automation berpotensi menimpa atau kehilangan versi lama;
- packaging membutuhkan installer/single-file.

Selain itu Sol boleh mengimplementasikan detail lokal tanpa menunggu Astra.
