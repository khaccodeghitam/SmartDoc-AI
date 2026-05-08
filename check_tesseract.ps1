$tesseractDir = "C:\Program Files\Tesseract-OCR"
$tesseractExe = "$tesseractDir\tesseract.exe"
$tessdataPath = "D:\sinh vien\OSSD\project\tessdata"
if (Test-Path $tesseractExe) {
    Write-Host "PASS: Found tesseract.exe"
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -notlike "*$tesseractDir*") {
        [Environment]::SetEnvironmentVariable("Path", "$userPath;$tesseractDir", "User")
        Write-Host "Updated User PATH."
    }
    [Environment]::SetEnvironmentVariable("TESSDATA_PREFIX", $tessdataPath, "User")
    $env:Path += ";$tesseractDir"
    $env:TESSDATA_PREFIX = $tessdataPath
    where.exe tesseract
    & $tesseractExe --version
    $langs = & $tesseractExe --list-langs
    $langs
    if ($langs -match "vie") { Write-Host "RESULT: Language 'vie' is present." } else { Write-Host "RESULT: Language 'vie' is MISSING." }
    Write-Host "FINAL STATUS: PASS"
} else {
    Write-Host "FAIL: Tesseract not found."
}
