# Funcao interna: espelha Source -> Dest com robocopy (0-7 ok, 8+ erro).
function Invoke-RobocopyMirror {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination,
        [int]$Retries = 30,
        [int]$WaitSeconds = 3,
        [string[]]$ExcludeDirs = @("database", "cache", "logs")
    )
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = "robocopy.exe"
    $excludeArg = ""
    if ($ExcludeDirs -and $ExcludeDirs.Count -gt 0) {
        $escaped = $ExcludeDirs | ForEach-Object { "`"$_`"" }
        $excludeArg = " /XD " + ($escaped -join " ")
    }
    $psi.Arguments = "`"$Source`" `"$Destination`" /MIR /R:$Retries /W:$WaitSeconds /NFL /NDL /NJH /NJS /NP$excludeArg"
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $p = [System.Diagnostics.Process]::Start($psi)
    $p.WaitForExit()
    return $p.ExitCode
}
