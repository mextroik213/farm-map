# update_site.ps1
$root      = Split-Path -Parent $MyInvocation.MyCommand.Path
$dataDir   = Join-Path $root "data"
$dataJs    = Join-Path $root "data.js"
$pyScript  = Join-Path $root "export_layers.py"
$qgisPy    = "C:\Program Files\QGIS 4.2.3\bin\python-qgis.bat"

Write-Host "=== Map update ===" -ForegroundColor Cyan

Write-Host "[1/2] QGIS export..." -ForegroundColor Yellow
& $qgisPy $pyScript
if ($LASTEXITCODE -ne 0) {
    Write-Host "Export failed." -ForegroundColor Red
    exit 1
}

Write-Host "[2/2] Building data.js..." -ForegroundColor Yellow

# Whitelist — точные имена файлов из папки data\
$whitelist = @(
  "Корпуса__сооружения_и_площадки",
  "Помещения_и_энергоузел",
  "Лагуны_1_и_2___контуры_прежней_карты",
  "В___сектора_и_подсектора",
  "Вода_и_помещения___проверить_привязку",
  "КЛ___колодцы_последнего_проекта",
  "КЛ___колодцы_старого_плана",
  "Р1_Р3___резервуары",
  "Скв1__Скв2__Скв3_нед____скважины",
  "Насосная_Станция",
  "Забор___линии",
  "Воздушные_участки___ЭЛ_",
  "Подземные_участки___ЭЛ_",
  "Опоры___ОП___рабочие_номера_",
  "НВ___контуры_объектов_по_генплану_2017",
  "НВ___сооружения_и_подписи",
  "Новые_места_уточнения___навоз_и_подземные_линии",
  "ГАЗ___Газопровод___сектора_и_участки",
  "СС___Подземная_связь___сектора_и_участки",
  "КН___Канализация___сектора_и_участки",
  "К1__К3__К3_1н___проектные_линии_2024"
)

$timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm")
$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine("// Auto-generated at $timestamp")
[void]$sb.AppendLine("const QGIS_DATA = {")

$matched = 0
Get-ChildItem $dataDir -Filter *.geojson | ForEach-Object {
    $key = $_.BaseName
    if ($whitelist -contains $key) {
        $content = Get-Content $_.FullName -Raw -Encoding UTF8
        [void]$sb.AppendLine("  `"$key`": $content,")
        Write-Host "  OK: $key" -ForegroundColor Green
        $matched++
    }
}
[void]$sb.AppendLine("};")

Set-Content -Path $dataJs -Value $sb.ToString() -Encoding UTF8

Write-Host ""
Write-Host "Matched: $matched of $($whitelist.Count)" -ForegroundColor Cyan
Write-Host "data.js: $dataJs" -ForegroundColor Green
Write-Host "Press F5 in browser" -ForegroundColor Green