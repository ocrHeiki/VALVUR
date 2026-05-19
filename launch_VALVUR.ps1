<#
###############################################################################
#                                                                             #
#   █████   █████           ████                                              #
#  ▒▒███   ▒▒███           ▒▒███                                              #
#   ▒███    ▒███   ██████   ▒███  █████ █████ █████ ████ ████████             #
#   ▒███    ▒███  ▒▒▒▒▒███  ▒███ ▒▒███ ▒▒███ ▒▒███ ▒███ ▒▒███▒▒███            #
#   ▒▒███   ███    ███████  ▒███  ▒███  ▒███  ▒███ ▒███   ▒███ ▒▒▒             #
#    ▒▒▒█████▒    ███▒▒███  ▒███  ▒▒███ ███   ▒███ ▒███   ▒███                #
#       ▒▒███     ▒▒████████ █████  ▒▒█████    ▒▒████████ █████               #
#        ▒▒▒       ▒▒▒▒▒▒▒▒ ▒▒▒▒▒    ▒▒▒▒▒      ▒▒▒▒▒▒▒▒ ▒▒▒▒▒                #
#                                                                             #
#   =======================================================================   #
#   |                                                                     |   #
#   |   PROJEKT:     VALVUR - Intsidendi süvaanalüüs                      |   #
#   |   FAILI NIMI:  launch_VALVUR.ps1                                    |   #
#   |   LOODUD:      2026-05-18                                           |   #
#   |   AUTOR:       Heiki Rebane                                         |   #
#   |   KIRJELDUS:   VALVUR-i kiirkäivitus Windowsis (PowerShell).        |   #
#   |                Kloonib repo, loob venv ja käivitab masteri.         |   #
#   |   GITHUB:      https://github.com/ocrHeiki/VALVUR                   |   #
#   |                                                                     |   #
#   =======================================================================   #
#                                                                             #
###############################################################################
#>

$REPO_URL = "https://github.com/ocrHeiki/VALVUR.git"

function Write-Banner {
    Write-Host "[*] VALVUR BOOTSTRAP ALUSTAB (PowerShell)" -ForegroundColor Cyan
    if ($env:KALI_IP) {
        Write-Host "[*] KALI IP: $($env:KALI_IP) (eksfiltreerimine aktiivne)" -ForegroundColor Green
    } else {
        Write-Host "[*] KALI IP: määramata (seadistad hiljem menüüst)" -ForegroundColor Yellow
    }
}

function Test-Command($cmd) {
    return (Get-Command $cmd -ErrorAction SilentlyContinue) -ne $null
}

function Main {
    Write-Banner

    # 1. Kontrolli git
    if (-not (Test-Command "git")) {
        Write-Host "[!] VIGA: Git pole paigaldatud!" -ForegroundColor Red
        Write-Host "    Laadi alla: https://git-scm.com/download/win"
        exit 1
    }

    # 2. Kontrolli python
    if (-not (Test-Command "python")) {
        Write-Host "[!] VIGA: Python 3 pole paigaldatud!" -ForegroundColor Red
        Write-Host "    Laadi alla: https://www.python.org/downloads/"
        exit 1
    }

    # 3. Ajutine töökaust
    $workDir = Join-Path $env:TEMP "VALVUR_LIVE"
    if (Test-Path $workDir) {
        Remove-Item -Recurse -Force $workDir -ErrorAction SilentlyContinue
    }
    New-Item -ItemType Directory -Force -Path $workDir | Out-Null
    Set-Location $workDir

    # 4. Kloonimine
    Write-Host "[*] Kloonitakse repositoorium: $REPO_URL" -ForegroundColor Cyan
    git clone $REPO_URL . 2>&1 | Out-Host
    if (-not (Test-Path ".\SKRIPTID\VALVUR_master.py")) {
        Write-Host "[!] VIGA: Kloonimine ebaõnnestus!" -ForegroundColor Red
        exit 1
    }

    # 5. Virtuaalkeskkonna loomine süsteemi pakettidega (juhuks kui internetti pole)
    Write-Host "[*] Luuakse isoleeritud virtuaalkeskkond (venv)..." -ForegroundColor Cyan
    python -m venv venv --system-site-packages
    $pythonExe = Join-Path $workDir "venv\Scripts\python.exe"
    if (-not (Test-Path $pythonExe)) {
        Write-Host "[!] VIGA: venv loomine ebaõnnestus!" -ForegroundColor Red
        exit 1
    }

    # 6. Sõltuvuste paigaldamine (kui võrk on olemas)
    Write-Host "[*] Kontrollitakse ja paigaldatakse sõltuvused..." -ForegroundColor Cyan
    try {
        & $pythonExe -m pip install python-evtx python-docx rich psutil --timeout 5 2>&1 | Out-Host
    } catch {
        Write-Host "[*] Hoiatus: Pip paigaldus ebaõnnestus, kasutatakse kohalikke pakette." -ForegroundColor Yellow
    }

    # 7. Käivitamine
    Write-Host "`n" + "="*60 -ForegroundColor Cyan
    Write-Host "   VALVUR KÄIVITUB VIRTUAALKESKKONNAS" -ForegroundColor Green
    Write-Host "   (interaktiivne master koos SCP eksfiltreerimisega)" -ForegroundColor Green
    Write-Host "="*60 + "`n" -ForegroundColor Cyan

    # Seadistame keskkonnamuutujad käimasolevas sessioonis
    if ($env:KALI_IP) {
        $env:KALI_IP = $env:KALI_IP
    }
    $env:VALVUR_OUT = Join-Path $workDir "TULEMUSED"

    # Käivitame Pythoni skripti otse ja puhtalt
    & $pythonExe "SKRIPTID\VALVUR_master.py"
}

Main
