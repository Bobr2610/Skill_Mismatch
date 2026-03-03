param(
    [ValidateSet("seminars", "report", "all")]
    [string]$Target = "all"
)

Write-Host "=== PDF Builder ===" -ForegroundColor Cyan
Write-Host ""

function Build-Seminars {
    Write-Host "[Seminars] Scanning files..." -ForegroundColor Cyan
    $semFiles = Get-ChildItem -Path "Seminars" -Filter "*.md" -ErrorAction SilentlyContinue |
        Sort-Object { [int]($_.BaseName -replace '\D+', '') }

    if (-not $semFiles -or $semFiles.Count -eq 0) {
        Write-Host "[Seminars] No markdown files found in Seminars/" -ForegroundColor Yellow
        return
    }

    $files = $semFiles | ForEach-Object { "Seminars/$($_.Name)" }
    Write-Host "[Seminars] Found $($files.Count) files" -ForegroundColor Gray

    pandoc $files `
        -o Seminars.pdf `
        --pdf-engine=xelatex `
        -V geometry:margin=0.5cm `
        -V 'mainfont=Cambria' `
        -V 'mathfont=Cambria Math' `
        -V 'monofont=Consolas' `
        -V pagestyle=empty `
        --from markdown+tex_math_single_backslash+tex_math_dollars-yaml_metadata_block

    if ($LASTEXITCODE -eq 0) {
        $file = Get-Item Seminars.pdf
        $sizeKB = [math]::Round($file.Length / 1024, 1)
        Write-Host ("[Seminars] OK: Seminars.pdf ({0} KB)" -f $sizeKB) -ForegroundColor Green
    } else {
        Write-Host "[Seminars] FAILED" -ForegroundColor Red
    }
}

function Build-Report {
    Write-Host "[Report] Scanning files..." -ForegroundColor Cyan
    $reportFiles = Get-ChildItem -Path "Report" -Filter "*.md" -ErrorAction SilentlyContinue |
        Sort-Object { $_.BaseName }

    if (-not $reportFiles -or $reportFiles.Count -eq 0) {
        Write-Host "[Report] No markdown files found in Report/" -ForegroundColor Yellow
        return
    }

    $files = $reportFiles | ForEach-Object { "Report/$($_.Name)" }
    Write-Host "[Report] Found $($files.Count) files:" -ForegroundColor Gray
    $files | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkGray }

    pandoc $files `
        -o "SkillMismatch_Report.pdf" `
        --pdf-engine=xelatex `
        --toc `
        --toc-depth=2 `
        -V documentclass=report `
        -V titlepage=true `
        -V geometry:margin=2.5cm `
        -V 'mainfont=Cambria' `
        -V 'mathfont=Cambria Math' `
        -V 'monofont=Consolas' `
        -V fontsize=12pt `
        -V linestretch=1.3 `
        -V linkcolor=blue `
        -V urlcolor=blue `
        -V toccolor=black `
        -V lang=ru `
        -V babel-lang=russian `
        -V 'header-includes=\usepackage{fancyhdr}\pagestyle{fancy}\fancyhead{}\fancyfoot{}\fancyfoot[C]{\thepage}\renewcommand{\headrulewidth}{0pt}\renewcommand{\footrulewidth}{0pt}\fancypagestyle{plain}{\fancyhf{}\fancyfoot[C]{\thepage}\renewcommand{\headrulewidth}{0pt}}\renewcommand{\contentsname}{Оглавление}\usepackage{titlesec}\titleformat{\chapter}[hang]{\Huge\bfseries}{}{0pt}{}\titlespacing*{\chapter}{0pt}{-20pt}{12pt}\titlespacing*{\section}{0pt}{16pt}{6pt}\titlespacing*{\subsection}{0pt}{12pt}{4pt}' `
        --from markdown+tex_math_single_backslash+tex_math_dollars+raw_tex `
        --highlight-style=tango

    if ($LASTEXITCODE -eq 0) {
        $file = Get-Item "SkillMismatch_Report.pdf"
        $sizeKB = [math]::Round($file.Length / 1024, 1)
        Write-Host ("[Report] OK: SkillMismatch_Report.pdf ({0} KB)" -f $sizeKB) -ForegroundColor Green
    } else {
        Write-Host "[Report] FAILED" -ForegroundColor Red
    }
}

switch ($Target) {
    "seminars" { Build-Seminars }
    "report"   { Build-Report }
    "all"      { Build-Seminars; Write-Host ""; Build-Report }
}

Write-Host ""
Write-Host "=== Done ===" -ForegroundColor Cyan
