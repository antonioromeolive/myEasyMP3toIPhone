# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

<#
I collegamenti del programma, eseguito da "Create shortcuts.cmd" e "Remove shortcuts.cmd" nella cartella sopra
(questo script sta nella sua cartella _internal, myEasyMP3toIPhone.spec).
  -Action Create   sblocca i file della cartella (Windows marca i file di uno zip scaricato da internet), poi crea il
                   collegamento nel menu Start; -Desktop Ask (chiede), Yes o No: anche sul desktop
  -Action Remove   cancella quei collegamenti (solo per nome)
I collegamenti puntano a questa cartella: dopo averla spostata, creali di nuovo.
#>
param(
    [ValidateSet("Create", "Remove")] [string]$Action = "Create",
    [ValidateSet("Ask", "Yes", "No")] [string]$Desktop = "Ask"
)
$ErrorActionPreference = "Stop"

$Folder = Split-Path -Parent $PSScriptRoot
$Name = "myEasyMP3toIPhone"
$Program = "myEasyMP3toIPhone.exe"
$MenuLink = Join-Path ([Environment]::GetFolderPath("Programs")) "$Name.lnk"
$DesktopLink = Join-Path ([Environment]::GetFolderPath("Desktop")) "$Name.lnk"

function New-ProgramShortcut([string]$Path) {
    $target = Join-Path $Folder $Program
    $shell = New-Object -ComObject WScript.Shell
    $link = $shell.CreateShortcut($Path)
    $link.TargetPath = $target
    $link.WorkingDirectory = $Folder
    $link.IconLocation = "$target,0"
    $link.Description = "Musica sul PC e sull'iPhone"
    $link.Save()
    Write-Host "Creato   $Path"
}

function Remove-ProgramShortcut([string]$Path) {
    if (Test-Path -LiteralPath $Path) {
        Remove-Item -LiteralPath $Path
        Write-Host "Tolto    $Path"
    }
}

if ($Action -eq "Create") {
    if (-not (Test-Path -LiteralPath (Join-Path $Folder $Program))) {
        throw "$Program non e' in $Folder : esegui lo script dalla cartella scompattata dallo zip"
    }
    Get-ChildItem -LiteralPath $Folder -Recurse -File | Unblock-File
    Write-Host "Sbloccati i file di $Folder"
    New-ProgramShortcut $MenuLink
    $onDesktop = $Desktop
    if ($onDesktop -eq "Ask") {
        $reply = Read-Host "Anche un collegamento sul desktop? [s/N]"
        if ($reply -match "^\s*(s|si|y|yes)\s*$") {
            $onDesktop = "Yes"
        } else {
            $onDesktop = "No"
        }
    }
    if ($onDesktop -eq "Yes") {
        New-ProgramShortcut $DesktopLink
    }
    Write-Host "Fatto: $Name e' nel menu Start."
} else {
    Remove-ProgramShortcut $MenuLink
    Remove-ProgramShortcut $DesktopLink
    Write-Host "Fatto. Per togliere anche il programma cancella la cartella $Folder"
}
