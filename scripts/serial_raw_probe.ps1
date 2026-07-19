param(
    [string]$Port = "COM6",
    [int[]]$BaudRates = @(9600, 4800, 2400, 1200, 19200, 38400, 57600, 115200),
    [string[]]$SerialModes = @("8N1", "7E1", "8E1", "7N1"),
    [string[]]$LineControls = @("Default", "Rts", "DtrRts", "None"),
    [string[]]$PollCommands = @("", "P`r`n", "W`r`n", "SI`r`n", "S`r`n", "Q`r`n"),
    [int]$Seconds = 2
)

$ErrorActionPreference = "Stop"

function Convert-SerialMode {
    param([string]$Mode)

    if ($Mode -notmatch "^([78])([NOE])([12])$") {
        throw "Modo serial invalido: $Mode"
    }

    $parity = switch ($Matches[2]) {
        "N" { [System.IO.Ports.Parity]::None }
        "E" { [System.IO.Ports.Parity]::Even }
        "O" { [System.IO.Ports.Parity]::Odd }
    }
    $stopBits = if ($Matches[3] -eq "2") {
        [System.IO.Ports.StopBits]::Two
    } else {
        [System.IO.Ports.StopBits]::One
    }

    return [pscustomobject]@{
        Label = $Mode
        DataBits = [int]$Matches[1]
        Parity = $parity
        StopBits = $stopBits
    }
}

function Convert-ToVisibleText {
    param([string]$Text)

    return ($Text.ToCharArray() | ForEach-Object {
        $code = [int][char]$_
        if ($code -ge 32 -and $code -le 126) { $_ } else { "." }
    }) -join ""
}

$modes = @($SerialModes | ForEach-Object { Convert-SerialMode $_ })

foreach ($baudRate in $BaudRates) {
    foreach ($mode in $modes) {
        foreach ($lineControl in $LineControls) {
            $serial = $null
            try {
                $serial = [System.IO.Ports.SerialPort]::new(
                    $Port,
                    $baudRate,
                    $mode.Parity,
                    $mode.DataBits,
                    $mode.StopBits
                )
                $serial.ReadTimeout = 250
                $serial.WriteTimeout = 250
                if ($lineControl -eq "Rts") {
                    $serial.RtsEnable = $true
                } elseif ($lineControl -eq "DtrRts") {
                    $serial.DtrEnable = $true
                    $serial.RtsEnable = $true
                } elseif ($lineControl -eq "None") {
                    $serial.DtrEnable = $false
                    $serial.RtsEnable = $false
                }
                $serial.Open()

                foreach ($command in $PollCommands) {
                    if ($command) {
                        try { $serial.Write($command) } catch {}
                    }
                    Start-Sleep -Milliseconds 120
                }

                $deadline = (Get-Date).AddSeconds($Seconds)
                $raw = ""
                while ((Get-Date) -lt $deadline) {
                    $raw += $serial.ReadExisting()
                    Start-Sleep -Milliseconds 100
                }

                if ($raw.Length -gt 0) {
                    Write-Host "RAW_FOUND $Port $baudRate $($mode.Label) $lineControl"
                    Write-Host (Convert-ToVisibleText $raw)
                    exit 0
                }
            } catch {
                Write-Host "NO_OPEN $Port $baudRate $($mode.Label) ${lineControl}: $($_.Exception.Message)"
            } finally {
                if ($serial -and $serial.IsOpen) {
                    $serial.Close()
                }
                if ($serial) {
                    $serial.Dispose()
                }
            }
        }
    }
}

Write-Host "RAW_NOT_FOUND $Port"
exit 2
