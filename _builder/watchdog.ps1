# ICD 知识库看门狗 - 监控 & 自动重启 4 个后台服务
# 用法: powershell -ExecutionPolicy Bypass -File watchdog.ps1

$ScriptRoot = Split-Path -Parent $PSCommandPath
$LogDir     = Join-Path $ScriptRoot "logs"
$null = New-Item -ItemType Directory -Path $LogDir -Force -ErrorAction SilentlyContinue

$Services = @(
    @{ Port=8765; Name="ICD"; Cmd="python"; Args="server_gzip.py";         Dir=Join-Path $ScriptRoot "web" }
    @{ Port=8766; Name="Drug"; Cmd="python"; Args="server.py";              Dir=Join-Path $ScriptRoot "drug" }
    @{ Port=8768; Name="Map";  Cmd="python"; Args="server.py";              Dir=Join-Path $ScriptRoot "4way-mapping" }
    @{ Port=8769; Name="Lit";  Cmd="python"; Args="server.py 8769";         Dir=Join-Path $ScriptRoot "literature" }
)

function Log($Msg) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$ts $Msg" | Out-File -Append -Encoding utf8 (Join-Path $LogDir "watchdog.log")
    Write-Host "$ts $Msg"
}

function Start-Svc($Svc) {
    $log = Join-Path $LogDir ("svc_" + $Svc.Port + ".log")
    $p = Start-Process -NoNewWindow -FilePath $Svc.Cmd -ArgumentList $Svc.Args -WorkingDirectory $Svc.Dir -PassThru -RedirectStandardOutput $log -RedirectStandardError $log
    Log (">> START " + $Svc.Name + " :" + $Svc.Port + " PID=" + $p.Id)
    return $p
}

function Test-PortOpen($Port) {
    try {
        $c = [System.Net.Sockets.TcpClient]::new()
        $t = $c.ConnectAsync('127.0.0.1', $Port)
        if ($t.Wait(3000)) {
            if ($c.Connected) { $c.Close(); return $true }
        }
        $c.Dispose()
    } catch {}
    return $false
}

# ---- 启动全部 ----
Log "=== Watchdog started ==="

$procs = @{}
foreach ($svc in $Services) {
    $procs[$svc.Port] = Start-Svc $svc
    Start-Sleep -Milliseconds 1500
}

Start-Sleep -Seconds 5
foreach ($svc in $Services) {
    $ok = Test-PortOpen $svc.Port
    $s = "OK"
    if (-not $ok) { $s = "FAIL" }
    Log ("  INIT " + $svc.Name + " :" + $svc.Port + " -> " + $s)
}

# ---- 监控循环 ----
while ($true) {
    Start-Sleep -Seconds 30

    foreach ($svc in $Services) {
        $p = $procs[$svc.Port]
        $exited = $p.HasExited
        $open = Test-PortOpen $svc.Port

        if ($exited) {
            Log ("!! CRASH " + $svc.Name + " :" + $svc.Port + " PID=" + $p.Id + " EXIT=" + $p.ExitCode + " restarting...")
        } elseif (-not $open) {
            Log ("!! STUCK " + $svc.Name + " :" + $svc.Port + " PID=" + $p.Id + " no response, killing...")
            Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
        } else {
            continue
        }

        $procs[$svc.Port] = Start-Svc $svc
        Start-Sleep -Seconds 3
        $ok = Test-PortOpen $svc.Port
        if ($ok) { Log ("  -> OK " + $svc.Name + " :" + $svc.Port) }
        else     { Log ("  -> FAIL " + $svc.Name + " :" + $svc.Port) }
    }

    # 每天 3:00 清理日志
    $now = Get-Date
    if ($now.Hour -eq 3 -and $now.Minute -lt 5) {
        Get-ChildItem $LogDir -Filter "*.log" | Where-Object { $_.Length -gt 5MB -or $_.LastWriteTime -lt (Get-Date).AddDays(-30) } | Remove-Item -Force -ErrorAction SilentlyContinue
        Log ("~~ Log cleanup done")
    }
}
