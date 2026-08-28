$ErrorActionPreference = 'Stop'

$repo = 'C:\Users\dauba1\Work\repos\pf-t332-t-aif-use2-c3-jobpack-project'
Set-Location $repo
conda activate maf

$gitHead = (git rev-parse HEAD).Trim()
$account = az account show --query "{name:name,id:id}" -o json | ConvertFrom-Json
if ($account.name -ne 'T332 - TCO') {
    throw "Wrong subscription: $($account.name)"
}

$startedUtc = [DateTime]::UtcNow.ToString('o')
$runStamp = [DateTime]::UtcNow.ToString('yyyyMMdd-HHmm')
$runId = "$runStamp-slice3"
$runRoot = Join-Path $repo 'maf\runs'
$runDir = Join-Path $runRoot $runId
New-Item -ItemType Directory -Force -Path $runDir | Out-Null

$tracker = Get-Content -Raw (Join-Path $repo 'maf\tracker_cases.json') | ConvertFrom-Json
$caseMap = @{}
foreach ($property in $tracker.PSObject.Properties) {
    $caseMap[$property.Name] = $property.Value
}

$summary = [pscustomobject]@{
    run_id = $runId
    started_utc = $startedUtc
    finished_utc = ''
    git_head = $gitHead
    azure_subscription = 'T332 - TCO'
    command = 'python -m maf.slice3'
    cases = New-Object System.Collections.ArrayList
}

function Save-Summary {
    $summaryPath = Join-Path $runDir 'summary.json'
    $summary | ConvertTo-Json -Depth 20 | Set-Content -Path $summaryPath -Encoding UTF8
}

function Get-CaseInfo {
    param([string]$Id)
    return $caseMap[$Id]
}

function Normalize-NpsToken {
    param([string]$Token)
    $clean = ($Token -replace '[^0-9/ ]', '').Trim()
    if (-not $clean) {
        return $null
    }
    return "$clean inch"
}

function Get-NpsFromLineNumber {
    param([string]$LineNumber)
    if (-not $LineNumber) {
        return $null
    }
    $firstLine = ($LineNumber -split "`r?`n")[0]
    $parts = $firstLine -split '-'
    for ($i = 0; $i -lt $parts.Count; $i++) {
        if ($parts[$i] -match '^\d{3}[A-Z]\d{2}$') {
            if ($i -gt 0) {
                return Normalize-NpsToken -Token $parts[$i - 1]
            }
        }
    }
    return $null
}

function Get-FollowUp {
    param(
        [string]$Id,
        $Missing
    )

    $info = Get-CaseInfo -Id $Id
    $missingSet = @($Missing) | Where-Object { $_ }
    $ordered = New-Object System.Collections.Generic.List[string]

    function Add-Part {
        param([string]$Text)
        if ($Text -and -not $ordered.Contains($Text)) {
            [void]$ordered.Add($Text)
        }
    }

    foreach ($field in @('scope_type', 'insulation', 'heat_tracing', 'dia_in', 'placeholders_TP')) {
        if ($missingSet -contains $field) {
            switch ($field) {
                'scope_type' {
                    switch ($info.cohort) {
                        'TLR single-removal' { Add-Part 'TLR removal and replace the damaged pipe section.' }
                        'TLR multi-removal' { Add-Part 'TLR removal and replace the damaged pipe section.' }
                        'Flange replacement' { Add-Part 'Flange replacement.' }
                        'Pipe section repl.' { Add-Part 'Replace the pipe section.' }
                        'Section + support' { Add-Part 'Replace the pipe section.' }
                        'Pipe extension' { Add-Part 'Pipe extension.' }
                        'Elbow replacement' { Add-Part 'Elbow replacement.' }
                        'Tee/branch repl.' { Add-Part 'Tee replacement.' }
                        default { Add-Part 'Replace the pipe section.' }
                    }
                }
                'insulation' {
                    if ($info.deducted_prompt -match 'Uninsulated|\bNI\b') {
                        Add-Part 'Uninsulated.'
                    }
                    else {
                        Add-Part 'Insulated.'
                    }
                }
                'heat_tracing' {
                    if ($info.deducted_prompt -match 'electric heat tracing') {
                        Add-Part 'electric heat tracing.'
                    }
                    elseif ($info.deducted_prompt -match 'no heat tracing') {
                        Add-Part 'no heat tracing.'
                    }
                    else {
                        Add-Part 'Process conditions remain TBD.'
                    }
                }
                'dia_in' {
                    $nps = Get-NpsFromLineNumber -LineNumber $info.line_number
                    if ($nps) {
                        Add-Part "Diameter $nps."
                    }
                }
                'placeholders_TP' {
                    Add-Part 'Tie-ins at TP-001 and TP-002.'
                }
            }
        }
    }

    foreach ($field in $missingSet) {
        if ($field -match 'pdes|poper|tdes|toper|process') {
            Add-Part 'Process conditions remain TBD.'
        }
    }

    if ($ordered.Count -eq 0) {
        Add-Part 'Process conditions remain TBD.'
    }

    return ($ordered -join ' ')
}

function Invoke-Turn {
    param(
        [string]$CaseId,
        [string]$Prompt,
        [string]$CaseDir,
        [int]$Turn
    )

    $stdoutPath = Join-Path $CaseDir ('turn-{0:D2}.json' -f $Turn)
    $stderrPath = Join-Path $CaseDir ('turn-{0:D2}.stderr.txt' -f $Turn)
    $process = Start-Process -FilePath 'python' -ArgumentList @(
        '-m', 'maf.slice3',
        '--history', (Join-Path $CaseDir 'history.json'),
        $Prompt
    ) -NoNewWindow -Wait -PassThru -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath
    return [pscustomobject]@{
        exitCode = $process.ExitCode
        stdoutPath = $stdoutPath
        stderrPath = $stderrPath
        stdoutText = if (Test-Path $stdoutPath) { Get-Content -Raw $stdoutPath } else { '' }
        stderrText = if (Test-Path $stderrPath) { Get-Content -Raw $stderrPath } else { '' }
    }
}

$expectedPackIds = @(
    'TC-001','TC-003','TC-005','TC-006','TC-008','TC-009','TC-010','TC-011','TC-012','TC-015',
    'TC-016','TC-017','TC-018','TC-019','TC-020','TC-021','TC-024','TC-025','TC-034'
)

try {
    for ($caseIndex = 1; $caseIndex -le 36; $caseIndex++) {
        $id = ('TC-{0:D3}' -f $caseIndex)
        $caseDir = Join-Path $runDir $id
        New-Item -ItemType Directory -Force -Path $caseDir | Out-Null

        $caseInfo = Get-CaseInfo -Id $id
        $followups = New-Object System.Collections.Generic.List[string]
        $turnCount = 0
        $asked = $false
        $unexpectedAsk = $false
        $stuck = $false
        $error = $null
        $missingFirst = @()
        $lastPayload = $null

        while ($turnCount -lt 6) {
            $turnNumber = $turnCount + 1
            if ($turnNumber -eq 1) {
                $prompt = $id
            }
            else {
                $prompt = $followups[$turnNumber - 2]
            }

            $result = Invoke-Turn -CaseId $id -Prompt $prompt -CaseDir $caseDir -Turn $turnNumber
            $turnCount++

            if ($result.exitCode -ne 0) {
                $error = $result.stderrText
                if (-not $error) {
                    $error = "Non-zero exit code $($result.exitCode) with empty stderr"
                }
                break
            }

            if (-not $result.stdoutText) {
                $error = 'Empty stdout from maf.slice3'
                break
            }

            try {
                $payload = $result.stdoutText | ConvertFrom-Json
            }
            catch {
                $error = "Failed to parse JSON from turn output: $($_.Exception.Message)`n`nSTDERR:`n$result.stderrText`n`nSTDOUT:`n$result.stdoutText"
                break
            }
            $lastPayload = $payload

            if ($turnNumber -eq 1) {
                $missingFirst = @($payload.missing)
                if (-not $payload.complete) {
                    $asked = $true
                    if ($expectedPackIds -contains $id) {
                        $unexpectedAsk = $true
                    }
                }
            }

            if ($payload.complete) {
                break
            }

            $nextFollowUp = Get-FollowUp -Id $id -Missing @($payload.missing)
            [void]$followups.Add($nextFollowUp)
        }

        if ($error -eq $null -and ($lastPayload -eq $null -or -not $lastPayload.complete) -and $turnCount -ge 6) {
            $stuck = $true
        }

        $caseObject = [pscustomobject]@{
            id = $id
            turns = $turnCount
            asked = $asked
            unexpected_ask = $unexpectedAsk
            complete_final = [bool]($lastPayload -and $lastPayload.complete)
            stuck = $stuck
            missing_first = $missingFirst
            followups = @($followups)
            wps_result = if ($lastPayload) { $lastPayload.wps_result } else { $null }
            nde_result = if ($lastPayload) { $lastPayload.nde_result } else { $null }
            material = if ($lastPayload) { $lastPayload.material } else { $null }
            answer_chars = if ($lastPayload -and $lastPayload.answer) { [int]$lastPayload.answer.Length } else { 0 }
            error = $error
        }

        [void]$summary.cases.Add($caseObject)
        Save-Summary

        if ($error) {
            Write-Host "[$id] error after $turnCount turn(s)"
        }
        elseif ($caseObject.complete_final) {
            Write-Host "[$id] complete in $turnCount turn(s)"
        }
        else {
            Write-Host "[$id] stuck after $turnCount turn(s)"
        }
    }
}
finally {
    $summary.finished_utc = [DateTime]::UtcNow.ToString('o')
    Save-Summary
    $zipPath = Join-Path $runRoot ($runId + '.zip')
    if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
    Compress-Archive -Path $runDir -DestinationPath $zipPath -Force

    $completeCount = ($summary.cases | Where-Object { $_.complete_final }).Count
    $stuckCount = ($summary.cases | Where-Object { $_.stuck }).Count
    $errorCount = ($summary.cases | Where-Object { $_.error }).Count
    Write-Host "Run directory: $runDir"
    Write-Host "Zip: $zipPath"
    Write-Host "Complete: $completeCount  Stuck: $stuckCount  Error: $errorCount"
}
