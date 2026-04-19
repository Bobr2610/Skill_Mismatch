param(
    [ValidateSet("report")]
    [string]$Target = "report"
)

Write-Host "=== PDF Builder ===" -ForegroundColor Cyan
Write-Host ""

function Build-Report {
    Write-Host "[Report] Scanning files..." -ForegroundColor Cyan
    $scriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { $PWD }
    $reportFiles = Get-ChildItem -Path "$scriptDir/Report" -Filter "*.md" -ErrorAction SilentlyContinue |
        Sort-Object { [int]($_.BaseName -replace '\D+', '') }

    if (-not $reportFiles -or $reportFiles.Count -eq 0) {
        Write-Host "[Report] No markdown files found in Report/" -ForegroundColor Yellow
        return
    }

    $files = $reportFiles | ForEach-Object { "$scriptDir/Report/$($_.Name)" }
    Write-Host "[Report] Found $($files.Count) files:" -ForegroundColor Gray
    $files | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkGray }

    pandoc $files `
        -o "$scriptDir/SkillMismatch_Report.pdf" `
        --pdf-engine=xelatex `
        --toc `
        --toc-depth=2 `
        -V documentclass=report `
        -V titlepage=true `
        -V geometry:margin=2.5cm `
        -V 'mainfont=Times New Roman' `
        -V 'sansfont=Arial' `
        -V 'monofont=Courier New' `
        -V fontsize=14pt `
        -V linestretch=1.5 `
        -V linkcolor=midnightblue `
        -V urlcolor=midnightblue `
        -V toccolor=black `
        -V lang=ru `
        -V babel-lang=russian `
        -V 'papersize=a4' `
        -V 'header-includes=\usepackage{titlesec}\titleformat{\chapter}{\Large\bfseries}{\thechapter.}{0.5em}{}\titlespacing*{\chapter}{0pt}{0pt}{20pt}\titleformat{\section}{\Large\bfseries}{\thesection.}{0.5em}{}\titlespacing*{\section}{0pt}{20pt}{10pt}\titleformat{\subsection}{\large\bfseries}{\thesubsection.}{0.5em}{}\titlespacing*{\subsection}{0pt}{15pt}{5pt}\pagestyle{plain}' `
        --from markdown+tex_math_single_backslash+tex_math_dollars+raw_tex `
        --syntax-highlighting=tango

    if ($LASTEXITCODE -eq 0) {
        $file = Get-Item "$scriptDir/SkillMismatch_Report.pdf"
        $sizeKB = [math]::Round($file.Length / 1024, 1)
        Write-Host ("[Report] OK: SkillMismatch_Report.pdf ({0} KB)" -f $sizeKB) -ForegroundColor Green
    } else {
        Write-Host "[Report] FAILED" -ForegroundColor Red
    }
}

switch ($Target) {
    "report"   { Build-Report }
}

Write-Host ""
Write-Host "=== Done ===" -ForegroundColor Cyan