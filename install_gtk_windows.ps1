# Скрипт для установки GTK+ на Windows (опционально)
# Этот скрипт помогает установить GTK+ для работы WeasyPrint на Windows

Write-Host "=== Установка GTK+ для WeasyPrint на Windows ===" -ForegroundColor Cyan
Write-Host ""

# Проверяем, установлен ли уже GTK+
$gtkPath = $env:GTK_BASEPATH
if ($gtkPath -and (Test-Path $gtkPath)) {
    Write-Host "✓ GTK+ уже установлен в: $gtkPath" -ForegroundColor Green
    exit 0
}

Write-Host "GTK+ не найден. Рекомендуемые способы установки:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Скачайте установщик GTK+ с:" -ForegroundColor White
Write-Host "   https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Или установите через MSYS2:" -ForegroundColor White
Write-Host "   https://www.msys2.org/" -ForegroundColor Cyan
Write-Host "   Затем выполните: pacman -S mingw-w64-x86_64-gtk3" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Или используйте conda (если установлен):" -ForegroundColor White
Write-Host "   conda install -c conda-forge weasyprint" -ForegroundColor Cyan
Write-Host ""
Write-Host "После установки перезапустите терминал и попробуйте снова." -ForegroundColor Yellow
