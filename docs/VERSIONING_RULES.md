# Prompt Action — Aturan Resmi Versioning & Continuity

Status: **CANONICAL RULES — SYSTEM V1**  
Legacy source: **V22.5.1**  
Baseline baru: **System V1 / Snapshot S001**

## 1. Prinsip utama

Prompt Action tidak memakai nomor panjang seperti `1.1.1.1.1`.

Gunakan tiga identitas terpisah:

- **System Version**: `V1`, `V2`, `V3`...
- **Snapshot**: `S001`, `S002`, `S003`...
- **Prompt Revision**: `R1`, `R2`, `R3`...

Aturan paling penting:

> Nama update mengikuti **PRIMARY CHANGE**, tetapi revision naik pada **semua prompt yang isi aktualnya berubah**.

## 2. Legacy V22.5.1

`V22.5.1` adalah **LEGACY SOURCE**, bukan nomor aktif Prompt Action.

Baseline System V1 memakai tujuh Prompt yang tetap identik dengan legacy V22.5.1. Prompt 3 memakai rilis resmi legacy `v22.5.2` yang telah diselesaikan sebelum normalisasi System V1. Rilis Prompt 3 tersebut dinormalkan sebagai **Prompt 3 V1 R1**, bukan sebagai R2/S002.

Seluruh baseline dinormalkan menjadi:

- System V1
- Snapshot S001
- Prompt 1A R1
- Prompt 1B R1
- Prompt 1B1 R1
- Prompt 1B2 R1
- Prompt 2 R1
- Prompt 3 R1
- Prompt 4 R1
- Prompt 5 R1

Riwayat sebelum V22.5.1 boleh disimpan sebagai arsip historis tetapi tidak ditampilkan sebagai cabang utama app.

## 3. System Version

System Version berubah hanya jika arsitektur/workflow global berubah secara material.

Contoh yang dapat memicu `V1 → V2`:

- struktur kerja 1B/1B1/1B2/Prompt 2/Prompt 3/Prompt 4/Prompt 5 berubah menyeluruh;
- format proyek/kontrak data global berubah;
- cara ownership visual, Jangkar, Narasi, audit, atau finalisasi dirombak secara fundamental;
- hampir semua prompt membutuhkan baseline baru karena satu perubahan sistemik.

Perubahan satu prompt, walaupun besar, **tidak otomatis** menaikkan System Version.

## 4. Snapshot

Snapshot adalah keadaan resmi seluruh System Version setelah satu release perubahan.

Contoh:

- `S001` — Baseline System V1
- `S002` — Update utama Prompt 3
- `S003` — Update utama Prompt 2
- `S004` — Update utama Prompt 3 berikutnya

Snapshot selalu naik satu nomor setiap release resmi.

Snapshot tidak boleh dianggap **COMPLETE** sebelum backup wajib selesai.

## 5. Prompt Revision

Revision dimiliki oleh masing-masing prompt.

Contoh Prompt 3:

`R1 → R2 → R3`

Contoh Prompt 2:

`R1 → R2`

Revision naik hanya bila isi aktual file prompt tersebut berubah.

Jika file tidak berubah, revision tetap.

## 6. PRIMARY CHANGE

PRIMARY CHANGE adalah prompt yang menjadi alasan utama release dibuat.

Contoh:

`S002 — Update Prompt 3`

Primary:

- Prompt 3 `R1 → R2`

Walaupun perubahan Prompt 3 memerlukan penyesuaian Prompt 1B2/4/5, nama release tetap **Update Prompt 3**.

## 7. SYNC / AFFECTED CHANGE

Prompt lain yang harus diubah agar tetap kompatibel disebut **SYNC CHANGE** atau **AFFECTED CHANGE**.

Contoh S002:

- Primary: Prompt 3 `R1 → R2`
- Sync: Prompt 1B2 `R1 → R2`
- Sync: Prompt 4 `R1 → R2`
- Sync: Prompt 5 `R1 → R2`

Revision prompt sync tetap naik karena file aktualnya berubah.

## 8. Contoh: Prompt 2 berubah setelah Prompt 3

Keadaan setelah S002 misalnya:

- Prompt 1A R1
- Prompt 1B R1
- Prompt 1B1 R1
- Prompt 1B2 R2
- Prompt 2 R1
- Prompt 3 R2
- Prompt 4 R2
- Prompt 5 R2

Lalu Prompt 2 diperbaiki dan Prompt 4 harus menyesuaikan:

`S003 — Update Prompt 2`

- Primary: Prompt 2 `R1 → R2`
- Sync: Prompt 4 `R2 → R3`

Prompt yang lain mempertahankan revision sebelumnya.

## 9. Contoh: Prompt 3 berubah lagi

`S004 — Update Prompt 3`

- Primary: Prompt 3 `R2 → R3`
- Sync: Prompt 1B2 `R2 → R3`
- Sync: Prompt 4 `R3 → R4` bila file Prompt 4 benar-benar berubah lagi

Revision tidak diseragamkan secara paksa. Setiap prompt membawa sejarahnya sendiri.

## 10. Draft dan eksperimen

Draft tidak masuk mainline resmi.

Contoh:

`Prompt 3 R2 → Draft A`

Draft boleh bercabang dari revision tertentu tetapi:

- tidak menjadi revision aktif;
- tidak membuat snapshot resmi;
- tidak mengganti file aktif;
- baru mendapat revision resmi bila dipromosikan melalui release.

## 11. Nama file

Gunakan pola:

`Prompt-<ID>_V<System>_R<Revision>.txt`

Contoh:

- `Prompt-3_V1_R1.txt`
- `Prompt-3_V1_R2.txt`
- `Prompt-2_V1_R2.txt`

Snapshot tidak perlu dimasukkan ke nama prompt karena snapshot merepresentasikan keadaan seluruh system, bukan identitas file prompt.

## 12. Metadata release

Setiap snapshot minimal mencatat:

- System Version
- Snapshot ID
- tanggal/waktu
- Primary Change
- revision sebelum → sesudah
- Sync/Affected Changes
- alasan perubahan
- ringkasan perubahan
- file yang berubah
- backup status
- SHA256 backup
- commit GitHub

## 13. Aturan backup wajib

Setiap release wajib:

1. arsipkan versi/revision lama;
2. simpan revision baru;
3. update version data;
4. update changelog;
5. update pohon versi app;
6. buat **FULL BACKUP ZIP** seluruh Prompt Action;
7. buat **SHA256**;
8. verifikasi ZIP;
9. simpan salinan kedua di lokasi lain;
10. baru tandai Snapshot **COMPLETE**.

GitHub tidak dihitung sebagai satu-satunya backup.

## 14. Rollback

Rollback tidak boleh menghapus sejarah.

Jika Prompt 3 R3 bermasalah dan perlu kembali memakai R2:

- R3 tetap disimpan sebagai riwayat;
- status aktif dapat menunjuk kembali ke R2 melalui snapshot recovery/rollback;
- catat alasan rollback;
- buat snapshot dan backup baru bila rollback dipromosikan sebagai keadaan resmi.

## 15. Tampilan app

App harus menyediakan tiga sudut pandang:

### Sejarah Sistem

`Legacy V22.5.1 → System V1 → System V2 ...`

### Snapshot Tree

Di dalam System V1:

`S001 → S002 → S003 → S004 ...`

### Per Prompt

Contoh Prompt 3:

`R1 → R2 → R3`

App tidak boleh menyamakan ketiga konsep tersebut menjadi satu angka versi panjang.

## 16. Aturan kesinambungan

- Prompt yang tidak berubah mempertahankan revision.
- Prompt sync yang isi file berubah wajib menaikkan revision.
- Primary Change menentukan nama release.
- Snapshot merekam keadaan semua prompt setelah release.
- System Version hanya berubah untuk perubahan sistemik.
- Semua histori lama dipertahankan dan dapat dilacak.
- Semua perubahan resmi wajib memiliki backup yang dapat dipulihkan tanpa GitHub.

## 17. Peran Astra dan Sol

**Astra** menentukan aturan versioning, kontrak data, primary/sync classification, UX pohon versi, risiko, dan acceptance criteria.

**Sol** mengimplementasikan perubahan, menguji, mengelola file/commit/build, membuat backup, memperbarui state, dan membuktikan hasil.

Satu perubahan belum dianggap selesai hanya karena source sudah diubah atau di-push. Status selesai mengikuti acceptance criteria + backup + bukti aktual.
