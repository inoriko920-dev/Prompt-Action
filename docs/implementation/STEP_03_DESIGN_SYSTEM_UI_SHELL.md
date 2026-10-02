# STEP 03 — DESIGN SYSTEM & UI SHELL

**Prompt Action — ASTRA → SOL**  
**Status:** HOLD — hanya boleh dieksekusi setelah STEP 00, STEP 01, STEP 02 PASS  
**Repo:** `inoriko920-dev/Prompt-Action`

> STEP 03 membangun bahasa visual dan shell aplikasi. Jangan implementasikan Dashboard final, Sejarah Sistem final, Per Prompt final, Backup final, Pengaturan final, backup/release engine, GitHub runtime sync, atau portable release.

## Gate sebelum mulai

1. STEP 00 = PASS.
2. STEP 01 = PASS.
3. STEP 02 = PASS.
4. Verifikasi live repo / branch / HEAD saat eksekusi.
5. Lima master UI reference dapat dibuka dan read-only.
6. Prompt/Legacy/Canonical version data protected.
7. Jika input wajib tidak dapat diverifikasi: STOP = BLOCKED.

## Master Visual Reference

Source of truth visual:

- `docs/UI_REFERENCE_PACKAGE_V1/materialized/images/01-Dashboard.jpg`
- `docs/UI_REFERENCE_PACKAGE_V1/materialized/images/02-Sejarah-Sistem.jpg`
- `docs/UI_REFERENCE_PACKAGE_V1/materialized/images/03-Per-Prompt.jpg`
- `docs/UI_REFERENCE_PACKAGE_V1/materialized/images/04-Backup-Recovery.jpg`
- `docs/UI_REFERENCE_PACKAGE_V1/materialized/images/05-Pengaturan.jpg`

### DESIGN LOCK

Semua halaman harus terasa sebagai satu aplikasi: sidebar width, topbar height, color scale, card radius, border, typography hierarchy, icon family, spacing rhythm, input height, button height, selected state, dan status badge konsisten. Tidak boleh redesign tanpa keputusan Astra/Product Owner.

## Tujuan

- centralized design tokens;
- reusable QML component library;
- MainWindow + Sidebar + Topbar + ContentHost;
- placeholder routes untuk 5 halaman;
- keyboard/focus/accessibility states;
- Windows DPI/responsive behavior;
- local icon/assets only;
- visual regression baseline + evidence.

## Scope boleh

- `src/prompt_action/ui/qml/theme/**`
- `src/prompt_action/ui/qml/components/**`
- `src/prompt_action/ui/qml/shell/**`
- `src/prompt_action/ui/qml/pages/Placeholder*.qml`
- `src/prompt_action/ui/assets/icons/**`
- `tests/step03/**`
- screenshot/visual evidence tooling
- docs STEP 03

## Scope terlarang

- Dashboard final;
- System/Snapshot tree final;
- Per Prompt final;
- Backup/Recovery final;
- Settings final business behavior;
- backup/release engine;
- GitHub runtime sync;
- portable release final;
- perubahan Prompt/Legacy/version_history canonical;
- runtime assets dari internet.

## Design token baseline

### Colors

- page background `#F4F8FD`
- surface `#FFFFFF`
- primary `#1677FF`
- primary strong `#0F6FEA`
- primary pale `#EAF4FF`
- text primary `#12213A`
- text secondary `#65758B`
- border `#D9E3F0`
- success `#1F9D62`
- warning `#D98A00`
- error `#C63B3B`

### Typography

- page title: 22–26 px semibold;
- section title: 16–18 px semibold;
- card title: 13–15 px semibold;
- body: 13–14 px regular;
- meta/caption: 11–12 px;
- button: 13 px semibold;
- hash/path: 11–12 px monospace.

Font policy: gunakan Windows/system-compatible font stack seperti Segoe UI bila tersedia. Jangan bundel/share font files.

### Spacing / radius

- spacing rhythm: 4 / 8 / 12 / 16 / 24 / 32 px;
- radius: 8 / 12 / 16 px;
- border default: 1 px subtle blue-gray;
- shadow sangat ringan.

## QML architecture target

```text
src/prompt_action/ui/qml/
├─ App.qml
├─ shell/
│  ├─ MainWindow.qml
│  ├─ Sidebar.qml
│  ├─ TopBar.qml
│  ├─ ContentHost.qml
│  └─ WindowChrome.qml
├─ theme/
│  ├─ Theme.qml
│  ├─ Metrics.qml
│  └─ Typography.qml
├─ components/
│  ├─ PAButton.qml
│  ├─ PACard.qml
│  ├─ PAInput.qml
│  ├─ PASearchField.qml
│  ├─ PABadge.qml
│  ├─ PAStatusPill.qml
│  ├─ PANavItem.qml
│  ├─ PASectionHeader.qml
│  ├─ PAIconButton.qml
│  ├─ PAEmptyState.qml
│  ├─ PAErrorBanner.qml
│  ├─ PASkeleton.qml
│  ├─ PATooltip.qml
│  └─ PADivider.qml
└─ pages/
   ├─ PlaceholderDashboard.qml
   ├─ PlaceholderSystemHistory.qml
   ├─ PlaceholderPrompt.qml
   ├─ PlaceholderBackup.qml
   └─ PlaceholderSettings.qml
```

Nama boleh berubah kecil, separation of concerns tidak boleh hilang.

## Component minimum states

- Button: default / hover / pressed / focus / disabled / loading.
- Card: default / selected / warning / error.
- Input/Search: empty / typing / focus / error / disabled.
- NavItem: default / hover / selected / focus.
- Badge/Status: neutral / success / warning / error / draft / legacy.
- IconButton: tooltip + accessible name.
- EmptyState, ErrorBanner, Skeleton, Tooltip, Divider.

## Main Window & Shell

- target utama: 1600×900;
- usable at 1920×1080 and 1366×768;
- baseline minimum sekitar 1180×720;
- resizable;
- sidebar deep-to-medium blue;
- content area pale blue-gray + white cards;
- topbar tanpa avatar/notif bell;
- topbar: page title/subtitle, Search, `System V1 • Sxxx`, backup health;
- 5 nav tetap: Dashboard, Sejarah Sistem, Per Prompt, Backup, Pengaturan;
- hanya satu selected nav;
- bottom status card `Siap bekerja`.

Search dan backup health pada STEP 03 hanya presentational/placeholder; behavior real ada pada step berikutnya.

## Placeholder route rule

Route: `dashboard | system_history | prompt | backup | settings`.

Placeholder harus jelas sebagai foundation build, misalnya `Dashboard content — STEP 04`. Dilarang membuat angka/version history palsu yang terlihat seperti data resmi.

## Interaction states

- Hover tidak mengubah ukuran/layout.
- Pressed tidak membuat jump.
- Focus ring jelas.
- Selected tidak bergantung warna saja.
- Disabled tidak menerima action.
- Loading mencegah duplicate action.
- Success/warning/error semantic, bukan dekorasi.

## Accessibility & keyboard

- deterministic Tab order;
- visible focus pada background putih/biru;
- icon-only control punya tooltip + accessibleName;
- status tidak hanya lewat warna;
- body text nyaman pada 100% DPI;
- hit target utama sekitar 40×40 px;
- Enter/Space mengaktifkan focused button;
- Escape menutup dismissable modal/tooltip.

## Responsive & DPI

Wajib diuji: 1920×1080 @100%, 1600×900 @100%, 1366×768 @100%, 125%, 150%, 175%, dan min window sekitar 1180×720.

Gunakan Qt high-DPI behavior. Jangan manual double-scale berbasis resolution.

## Asset policy

- local SVG/vector assets;
- satu icon family;
- tidak ada CDN/web image runtime;
- tidak ada emoji sebagai icon utama;
- assets harus resolve dari cwd lain dan setelah relocation.

## Visual regression evidence

```text
evidence/step03/
├─ screenshots/
│  ├─ 1600x900_100_dashboard-shell.png
│  ├─ 1600x900_100_history-shell.png
│  ├─ 1600x900_100_prompt-shell.png
│  ├─ 1600x900_100_backup-shell.png
│  └─ 1600x900_100_settings-shell.png
├─ components/
│  ├─ buttons_states.png
│  ├─ inputs_states.png
│  ├─ nav_states.png
│  └─ status_badges.png
└─ visual_review.md
```

Perbedaan dari master harus diklasifikasikan: expected technical adaptation / defect / deferred.

## Test T01–T30

1. Theme singleton load tanpa QML error.
2. Token utama dapat diakses komponen.
3. Button primary states.
4. Button secondary/disabled/loading.
5. Card states.
6. Input states.
7. SearchField layout.
8. NavItem states.
9. Status badge states.
10. IconButton tooltip/accessibility.
11. MainWindow 1600×900.
12. Min window 1180×720.
13. 1366×768.
14. 125% DPI.
15. 150% DPI.
16. 175% DPI.
17. Keyboard Tab order.
18. Enter/Space activation.
19. Dashboard placeholder route.
20. System History placeholder route.
21. Per Prompt placeholder route.
22. Backup placeholder route.
23. Settings placeholder route.
24. Topbar title/subtitle mengikuti route.
25. Sidebar hanya satu selected item.
26. No QML warning/error saat navigasi normal.
27. Local asset resolution dari non-project cwd.
28. Relocation tetap resolve assets.
29. Protected Prompt/Legacy/version data unchanged.
30. Screenshot/evidence set complete.

## Blocking failure

- missing type/resource/binding loop;
- sidebar/topbar clipped;
- keyboard/focus broken;
- scattered hardcoded styling;
- visual language melenceng signifikan;
- protected source berubah;
- runtime asset dari internet;
- DPI 125/150% overlap signifikan.

## Acceptance Gate

PASS hanya jika STEP 00–02 PASS, token centralized, minimum component library + states lengkap, shell routing stabil, visual parity sesuai master tanpa redesign, responsive/DPI usable, keyboard/focus/accessibility lulus, no blocking QML warning/error, protected source unchanged, dan T01–T30 + screenshot/diff evidence lengkap.

Jika satu blocking gate gagal: **FAIL/BLOCKED**. Jangan lanjut STEP 04.

## Prompt eksekusi untuk Sol

```text
PERAN AKTIF: SOL.

Kerjakan STEP 03 — DESIGN SYSTEM & UI SHELL untuk repo inoriko920-dev/Prompt-Action berdasarkan DOCX/Markdown STEP 03, master implementation plan, dan 5 MASTER UI REFERENCE di docs/UI_REFERENCE_PACKAGE_V1/materialized/images/. Kerjakan sendiri secara SERIAL.

Sebelum implementasi:
1. buktikan STEP 00, STEP 01, dan STEP 02 berstatus PASS;
2. verifikasi live repo/branch/HEAD; jangan mengandalkan planning SHA jika repo berubah;
3. pastikan Prompt/Legacy/Canonical version data dan master UI reference tetap protected/read-only.

Scope STEP 03 hanya: design tokens/theme, reusable QML components, MainWindow, Sidebar, Topbar, ContentHost, placeholder routes, local icons/assets, keyboard/focus/accessibility states, DPI/responsive handling, visual regression/evidence.

Jangan implementasikan Dashboard final, Sejarah Sistem final, Per Prompt final, Backup UI final, Pengaturan final, backup/release engine, GitHub runtime sync, atau portable release. Jangan ubah prompt/legacy/version_history canonical.

Gunakan visual putih-biru profesional yang sudah dikunci. Tidak boleh redesign. Jalankan T01–T30, ambil screenshot evidence, cek QML warning/error, cek protected-source diff, lalu keluarkan laporan PASS/FAIL/BLOCKED. Jika prerequisite belum PASS atau input wajib tidak dapat diverifikasi: STOP.
```