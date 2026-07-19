param(
    [string]$ServerUrl = "http://127.0.0.1:8000",
    [string]$EnvFile = "",
    [string[]]$Ports = @(),
    [int[]]$BaudRates = @(9600, 4800, 2400, 1200, 19200, 38400, 57600, 115200),
    [string[]]$SerialModes = @("8N1", "7E1", "8E1", "7N1"),
    [string[]]$LineControls = @("Default", "Rts", "DtrRts", "None"),
    [string[]]$PollCommands = @("", "P`r`n", "W`r`n", "SI`r`n", "S`r`n", "Q`r`n", "PRINT`r`n"),
    [int]$ProbeSeconds = 4,
    [int]$RescanSeconds = 3,
    [int]$ReadPauseMs = 120,
    [int]$PostCooldownMs = 900,
    [int]$StableSamples = 3,
    [decimal]$StableToleranceKg = 0.020,
    [switch]$ListPorts,
    [switch]$Once
)

$ErrorActionPreference = "Stop"

function Get-ProjectRoot {
    return (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

function Read-DotEnvFile {
    param([string]$Path)

    $values = @{}
    if (-not (Test-Path -LiteralPath $Path)) {
        return $values
    }

    foreach ($line in Get-Content -LiteralPath $Path) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("#") -or -not $trimmed.Contains("=")) {
            continue
        }

        $parts = $trimmed.Split("=", 2)
        $name = $parts[0].Trim()
        $value = $parts[1].Trim()
        if (
            ($value.StartsWith('"') -and $value.EndsWith('"')) -or
            ($value.StartsWith("'") -and $value.EndsWith("'"))
        ) {
            $value = $value.Substring(1, $value.Length - 2)
        }
        $values[$name] = $value
    }

    return $values
}

function Get-EnvValue {
    param(
        [hashtable]$DotEnv,
        [string]$Name,
        [string]$Default = ""
    )

    $processValue = [Environment]::GetEnvironmentVariable($Name, "Process")
    if ($processValue) {
        return $processValue
    }
    if ($DotEnv.ContainsKey($Name) -and $DotEnv[$Name]) {
        return $DotEnv[$Name]
    }
    return $Default
}

function Convert-CsvToStringArray {
    param([string]$Value)
    if (-not $Value) {
        return @()
    }
    return @($Value.Split(",") | ForEach-Object { $_.Trim() } | Where-Object { $_ })
}

function Convert-CsvToIntArray {
    param([string]$Value)
    $items = @()
    foreach ($item in (Convert-CsvToStringArray -Value $Value)) {
        $parsed = 0
        if ([int]::TryParse($item, [ref]$parsed) -and $parsed -gt 0) {
            $items += $parsed
        }
    }
    return $items
}

function Convert-EscapedSerialCommand {
    param([string]$Value)
    return $Value.Replace('\r', "`r").Replace('\n', "`n").Replace('\t', "`t")
}

function Join-Url {
    param([string]$BaseUrl, [string]$Path)
    return $BaseUrl.TrimEnd("/") + "/" + $Path.TrimStart("/")
}

function Get-SerialPorts {
    param([string[]]$PreferredPorts)

    if ($PreferredPorts -and $PreferredPorts.Count -gt 0) {
        return $PreferredPorts
    }

    $found = [System.IO.Ports.SerialPort]::GetPortNames()
    return $found | Sort-Object {
        if ($_ -match "COM(\d+)") { [int]$Matches[1] } else { 9999 }
    }, { $_ }
}

function Get-PortDescriptions {
    $descriptions = @{}
    try {
        $devices = Get-CimInstance Win32_PnPEntity | Where-Object { $_.Name -match "\(COM\d+\)" }
        foreach ($device in $devices) {
            if ($device.Name -match "(COM\d+)") {
                $descriptions[$Matches[1]] = $device.Name
            }
        }
    } catch {
        # Descriptions are optional.
    }
    return $descriptions
}

function Convert-SerialMode {
    param([string]$Mode)

    if ($Mode -notmatch "^([78])([NOE])([12])$") {
        throw "Modo serial invalido: $Mode. Use formatos como 8N1 o 7E1."
    }

    $dataBits = [int]$Matches[1]
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
        DataBits = $dataBits
        Parity = $parity
        StopBits = $stopBits
    }
}

function Get-WeightKgText {
    param([string]$Text)

    $matches = [regex]::Matches(
        $Text,
        # Require an explicit unit so corrupted serial bytes such as HRo7)
        # cannot be interpreted as a 7 kg reading.
        "(?<value>-?\d+(?:[\.,]\d+)?)\s*(?<unit>kilogramos?|kgs?|gramos?|gr|g)",
        [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
    )
    if ($matches.Count -eq 0) {
        return $null
    }

    # Use the last number; most scales send status text before the weight.
    $match = $matches[$matches.Count - 1]
    $valueText = $match.Groups["value"].Value.Replace(",", ".")
    $parsed = 0.0
    $ok = [double]::TryParse(
        $valueText,
        [System.Globalization.NumberStyles]::Float,
        [System.Globalization.CultureInfo]::InvariantCulture,
        [ref]$parsed
    )
    if (-not $ok) {
        return $null
    }

    $unit = $match.Groups["unit"].Value.ToLowerInvariant()
    if ($unit -in @("g", "gr", "gramo", "gramos")) {
        $parsed = $parsed / 1000.0
    }

    return $parsed.ToString("0.000", [System.Globalization.CultureInfo]::InvariantCulture)
}

function Test-ValidWeight {
    param([string]$TextValue, [decimal]$MaxWeightKg)

    $parsed = 0.0
    $ok = [double]::TryParse(
        $TextValue,
        [System.Globalization.NumberStyles]::Float,
        [System.Globalization.CultureInfo]::InvariantCulture,
        [ref]$parsed
    )

    return $ok -and $parsed -gt 0 -and $parsed -le [double]$MaxWeightKg
}

function Test-StableWeight {
    param(
        [System.Collections.Generic.List[decimal]]$Samples,
        [int]$RequiredSamples,
        [decimal]$ToleranceKg
    )

    if ($Samples.Count -lt $RequiredSamples) {
        return $false
    }

    $start = $Samples.Count - $RequiredSamples
    $window = $Samples.GetRange($start, $RequiredSamples)
    $min = ($window | Measure-Object -Minimum).Minimum
    $max = ($window | Measure-Object -Maximum).Maximum
    return ([decimal]$max - [decimal]$min) -le $ToleranceKg
}

function Send-Weight {
    param(
        [string]$Endpoint,
        [string]$Token,
        [string]$Weight,
        [string]$DeviceName,
        [string]$RawData
    )

    $payload = @{
        weight_kg = $Weight
        device_name = $DeviceName
        raw_data = $RawData
        is_stable = $true
    } | ConvertTo-Json -Compress

    Invoke-RestMethod `
        -Method Post `
        -Uri $Endpoint `
        -Headers @{ "X-Weight-Token" = $Token } `
        -ContentType "application/json" `
        -Body $payload | Out-Null
}

function Open-SerialPort {
    param(
        [string]$PortName,
        [int]$BaudRate,
        [pscustomobject]$SerialMode,
        [string]$LineControl
    )

    $serial = [System.IO.Ports.SerialPort]::new(
        $PortName,
        $BaudRate,
        $SerialMode.Parity,
        $SerialMode.DataBits,
        $SerialMode.StopBits
    )
    $serial.ReadTimeout = 500
    $serial.WriteTimeout = 500
    if ($LineControl -eq "Rts") {
        $serial.RtsEnable = $true
    } elseif ($LineControl -eq "DtrRts") {
        $serial.DtrEnable = $true
        $serial.RtsEnable = $true
    } elseif ($LineControl -eq "None") {
        $serial.DtrEnable = $false
        $serial.RtsEnable = $false
    }
    $serial.Open()
    Start-Sleep -Milliseconds 350
    try { $serial.DiscardInBuffer() } catch {}
    return $serial
}

function Send-PollCommands {
    param(
        [System.IO.Ports.SerialPort]$Serial,
        [string[]]$Commands
    )

    foreach ($command in $Commands) {
        if (-not $command) {
            continue
        }

        try {
            $Serial.Write($command)
            Start-Sleep -Milliseconds 80
        } catch {
            # Ignore commands unsupported by a specific balance.
        }
    }
}

function Read-SerialChunk {
    param([System.IO.Ports.SerialPort]$Serial)

    try {
        return $Serial.ReadExisting()
    } catch [TimeoutException] {
        return ""
    }
}

function Watch-SerialPort {
    param(
        [string]$PortName,
        [int]$BaudRate,
        [pscustomobject]$SerialMode,
        [string]$LineControl,
        [string]$Endpoint,
        [string]$Token,
        [decimal]$MaxWeightKg
    )

    $serial = $null
    $deviceName = "$PortName@$BaudRate/$($SerialMode.Label)/$LineControl"
    $lastSent = ""
    $lastSentAt = Get-Date "2000-01-01"
    $lastPollAt = Get-Date "2000-01-01"
    $buffer = ""
    $samples = [System.Collections.Generic.List[decimal]]::new()

    try {
        $serial = Open-SerialPort -PortName $PortName -BaudRate $BaudRate -SerialMode $SerialMode -LineControl $LineControl
        Write-Host "Conectado a $deviceName. Esperando lectura real..."
        Send-PollCommands -Serial $serial -Commands $PollCommands

        while ($serial.IsOpen) {
            $chunk = Read-SerialChunk -Serial $serial
            if ($chunk) {
                $buffer = ($buffer + " " + $chunk)
                if ($buffer.Length -gt 500) {
                    $buffer = $buffer.Substring($buffer.Length - 500)
                }

                $weight = Get-WeightKgText -Text $buffer
                if ($weight -and (Test-ValidWeight -TextValue $weight -MaxWeightKg $MaxWeightKg)) {
                    $weightDecimal = [decimal]::Parse($weight, [System.Globalization.CultureInfo]::InvariantCulture)
                    $samples.Add($weightDecimal)
                    while ($samples.Count -gt [Math]::Max($StableSamples, 1)) {
                        $samples.RemoveAt(0)
                    }
                    if (-not (Test-StableWeight -Samples $samples -RequiredSamples ([Math]::Max($StableSamples, 1)) -ToleranceKg $StableToleranceKg)) {
                        continue
                    }

                    $now = Get-Date
                    $cooldownOk = (($now - $lastSentAt).TotalMilliseconds -ge $PostCooldownMs)
                    if ($weight -ne $lastSent -or $cooldownOk) {
                        try {
                            Send-Weight -Endpoint $Endpoint -Token $Token -Weight $weight -DeviceName $deviceName -RawData $buffer.Trim()
                            Write-Host "Peso enviado desde ${deviceName}: $weight kg"
                            $lastSent = $weight
                            $lastSentAt = $now
                        } catch {
                            Write-Host "No se pudo enviar a Django: $($_.Exception.Message)"
                        }
                    }
                }
            } elseif (((Get-Date) - $lastPollAt).TotalMilliseconds -ge 1200) {
                Send-PollCommands -Serial $serial -Commands $PollCommands
                $lastPollAt = Get-Date
            }

            Start-Sleep -Milliseconds $ReadPauseMs
        }
    } catch {
        Write-Host "Conexion de balanza perdida en ${deviceName}: $($_.Exception.Message)"
    } finally {
        if ($serial -and $serial.IsOpen) {
            $serial.Close()
        }
        if ($serial) {
            $serial.Dispose()
        }
    }
}

function Probe-SerialPort {
    param(
        [string]$PortName,
        [int]$BaudRate,
        [pscustomobject]$SerialMode,
        [string]$LineControl,
        [decimal]$MaxWeightKg
    )

    $serial = $null
    $buffer = ""
    try {
        $serial = Open-SerialPort -PortName $PortName -BaudRate $BaudRate -SerialMode $SerialMode -LineControl $LineControl
        Send-PollCommands -Serial $serial -Commands $PollCommands
        $lastPollAt = Get-Date
        $deadline = (Get-Date).AddSeconds($ProbeSeconds)
        while ((Get-Date) -lt $deadline) {
            $chunk = Read-SerialChunk -Serial $serial
            if ($chunk) {
                $buffer = ($buffer + " " + $chunk)
                $weight = Get-WeightKgText -Text $buffer
                if ($weight -and (Test-ValidWeight -TextValue $weight -MaxWeightKg $MaxWeightKg)) {
                    return $true
                }
            } elseif (((Get-Date) - $lastPollAt).TotalMilliseconds -ge 900) {
                Send-PollCommands -Serial $serial -Commands $PollCommands
                $lastPollAt = Get-Date
            }
            Start-Sleep -Milliseconds $ReadPauseMs
        }
        return $false
    } catch {
        Write-Host "No se pudo probar ${PortName}@$BaudRate/$($SerialMode.Label)/${LineControl}: $($_.Exception.Message)"
        return $false
    } finally {
        if ($serial -and $serial.IsOpen) {
            $serial.Close()
        }
        if ($serial) {
            $serial.Dispose()
        }
    }
}

$projectRoot = Get-ProjectRoot
if (-not $EnvFile) {
    $EnvFile = Join-Path $projectRoot ".env"
}

$dotEnv = Read-DotEnvFile -Path $EnvFile

if (-not $PSBoundParameters.ContainsKey("Ports")) {
    $envPorts = Convert-CsvToStringArray -Value (Get-EnvValue -DotEnv $dotEnv -Name "BALANZA_SERIAL_PORTS")
    if ($envPorts.Count -gt 0) {
        $Ports = $envPorts
    }
}
if (-not $PSBoundParameters.ContainsKey("BaudRates")) {
    $envBaudRates = Convert-CsvToIntArray -Value (Get-EnvValue -DotEnv $dotEnv -Name "BALANZA_SERIAL_BAUDRATES")
    if ($envBaudRates.Count -gt 0) {
        $BaudRates = $envBaudRates
    }
}
if (-not $PSBoundParameters.ContainsKey("SerialModes")) {
    $envSerialModes = Convert-CsvToStringArray -Value (Get-EnvValue -DotEnv $dotEnv -Name "BALANZA_SERIAL_MODES")
    if ($envSerialModes.Count -gt 0) {
        $SerialModes = $envSerialModes
    }
}
if (-not $PSBoundParameters.ContainsKey("LineControls")) {
    $envLineControls = Convert-CsvToStringArray -Value (Get-EnvValue -DotEnv $dotEnv -Name "BALANZA_LINE_CONTROLS")
    if ($envLineControls.Count -gt 0) {
        $LineControls = $envLineControls | ForEach-Object {
            if ($_ -eq "dtr_rts") { "DtrRts" } else { $_ }
        }
    }
}
if (-not $PSBoundParameters.ContainsKey("PollCommands")) {
    $envPollCommands = Convert-CsvToStringArray -Value (Get-EnvValue -DotEnv $dotEnv -Name "BALANZA_POLL_COMMANDS")
    if ($envPollCommands.Count -gt 0) {
        $PollCommands = @($envPollCommands | ForEach-Object {
            Convert-EscapedSerialCommand -Value $_
        })
    }
}
if (-not $PSBoundParameters.ContainsKey("ProbeSeconds")) {
    $ProbeSeconds = [int](Get-EnvValue -DotEnv $dotEnv -Name "BALANZA_READ_SECONDS" -Default $ProbeSeconds)
}
if (-not $PSBoundParameters.ContainsKey("StableSamples")) {
    $StableSamples = [int](Get-EnvValue -DotEnv $dotEnv -Name "BALANZA_STABLE_SAMPLES" -Default $StableSamples)
}
if (-not $PSBoundParameters.ContainsKey("StableToleranceKg")) {
    $StableToleranceKg = [decimal]::Parse(
        (Get-EnvValue -DotEnv $dotEnv -Name "BALANZA_STABLE_TOLERANCE_KG" -Default $StableToleranceKg),
        [System.Globalization.CultureInfo]::InvariantCulture
    )
}

$apiPath = Get-EnvValue -DotEnv $dotEnv -Name "DJANGO_WEIGHT_UPDATE_URL" -Default "/api/update_weight/"
$token = Get-EnvValue -DotEnv $dotEnv -Name "WEIGHT_API_TOKEN"
$maxWeightText = Get-EnvValue -DotEnv $dotEnv -Name "MAX_WEIGHT_KG" -Default "1000"
$maxWeightKg = [decimal]::Parse($maxWeightText, [System.Globalization.CultureInfo]::InvariantCulture)
$endpoint = Join-Url -BaseUrl $ServerUrl -Path $apiPath
$modeConfigs = @($SerialModes | ForEach-Object { Convert-SerialMode -Mode $_ })

if (-not $token) {
    throw "WEIGHT_API_TOKEN no esta configurado. Revise .env o defina la variable de entorno."
}

if ($ListPorts) {
    $available = Get-SerialPorts -PreferredPorts $Ports
    $descriptions = Get-PortDescriptions
    if (-not $available -or $available.Count -eq 0) {
        Write-Host "No hay puertos COM disponibles."
    } else {
        Write-Host "Puertos COM disponibles:"
        $available | ForEach-Object {
            $description = if ($descriptions.ContainsKey($_)) { $descriptions[$_] } else { "sin descripcion" }
            Write-Host " - $_ : $description"
        }
    }
    exit 0
}

Write-Host "Puente de balanza iniciado."
Write-Host "Endpoint Django: $endpoint"
Write-Host "Velocidades: $($BaudRates -join ', ')"
Write-Host "Modos seriales: $($SerialModes -join ', ')"
Write-Host "Controles de linea: $($LineControls -join ', ')"
Write-Host "Estabilidad: $StableSamples muestras, tolerancia $StableToleranceKg kg"
Write-Host "Presione Ctrl+C para detener."

do {
    $availablePorts = Get-SerialPorts -PreferredPorts $Ports
    if (-not $availablePorts -or $availablePorts.Count -eq 0) {
        if ($Once) {
            Write-Host "No hay puertos COM disponibles."
            exit 2
        }
        Write-Host "No hay puertos COM disponibles. Reintentando en $RescanSeconds segundos..."
        Start-Sleep -Seconds $RescanSeconds
        continue
    }

    foreach ($portName in $availablePorts) {
        foreach ($baudRate in $BaudRates) {
            foreach ($modeConfig in $modeConfigs) {
                foreach ($lineControl in $LineControls) {
                    Write-Host "Probando $portName a $baudRate baudios ($($modeConfig.Label), $lineControl)..."
                    if (Probe-SerialPort -PortName $portName -BaudRate $baudRate -SerialMode $modeConfig -LineControl $lineControl -MaxWeightKg $maxWeightKg) {
                        if ($Once) {
                            Write-Host "Balanza detectada en $portName a $baudRate baudios ($($modeConfig.Label), $lineControl)."
                            exit 0
                        }
                        Watch-SerialPort -PortName $portName -BaudRate $baudRate -SerialMode $modeConfig -LineControl $lineControl -Endpoint $endpoint -Token $token -MaxWeightKg $maxWeightKg
                    }
                }
            }
        }
    }

    if ($Once) {
        Write-Host "No se detecto lectura de balanza en los puertos disponibles."
        exit 2
    }

    Write-Host "No se detecto lectura. Reintentando en $RescanSeconds segundos..."
    Start-Sleep -Seconds $RescanSeconds
} while ($true)
