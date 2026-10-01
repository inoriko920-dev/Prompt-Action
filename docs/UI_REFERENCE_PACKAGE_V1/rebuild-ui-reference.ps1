$ErrorActionPreference = "Stop"
$expected = "514a01befbfe50946431b82aa0bcf03415fa36460976b1db2091da65024a7799"
$parts = Get-ChildItem -Path $PSScriptRoot -Filter "part-*.b64" | Sort-Object Name
if ($parts.Count -eq 0) { throw "Part Base64 tidak ditemukan." }
$base64 = ($parts | ForEach-Object { Get-Content $_.FullName -Raw }) -join ""
$bytes = [Convert]::FromBase64String($base64)
$out = Join-Path $PSScriptRoot "Prompt-Action-UI-Reference-Package-V1.zip"
[IO.File]::WriteAllBytes($out, $bytes)
$actual = (Get-FileHash $out -Algorithm SHA256).Hash.ToLower()
if ($actual -ne $expected) { throw "SHA256 tidak cocok. Expected=$expected Actual=$actual" }
Write-Host "OK: ZIP berhasil direkonstruksi dan SHA256 valid."
Write-Host $out
