# Update all installed Claude Code plugins.
#
# Refreshes every configured marketplace, then runs `claude plugin update` for
# each installed plugin in its own scope. Emits a per-plugin status line and a
# summary at the end. Exit code is nonzero if any plugin update failed.

Write-Host "Refreshing marketplaces..."
claude plugin marketplace update
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Marketplace refresh exited with code $LASTEXITCODE - continuing."
}

Write-Host ""
Write-Host "Enumerating installed plugins..."
$json = claude plugin list --json
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to list plugins (exit $LASTEXITCODE)."
    exit 1
}

$plugins = $json | ConvertFrom-Json
if (-not $plugins -or @($plugins).Count -eq 0) {
    Write-Host "No plugins installed."
    exit 0
}

$updated = New-Object System.Collections.Generic.List[string]
$current = New-Object System.Collections.Generic.List[string]
$failed  = New-Object System.Collections.Generic.List[string]

foreach ($p in $plugins) {
    Write-Host ""
    Write-Host "-> $($p.id) [scope=$($p.scope), version=$($p.version)]"
    $output = (claude plugin update $p.id --scope $p.scope) | Out-String
    $exit = $LASTEXITCODE
    Write-Host $output.TrimEnd()

    if ($exit -ne 0) {
        $failed.Add($p.id)
    } elseif ($output -match 'updated from') {
        $updated.Add($p.id)
    } elseif ($output -match 'already at the latest') {
        $current.Add($p.id)
    } else {
        # Unrecognized success output - treat as failed so it surfaces.
        $failed.Add($p.id)
    }
}

Write-Host ""
Write-Host "===== Summary ====="
Write-Host "Updated:        $($updated.Count)"
foreach ($id in $updated) { Write-Host "  - $id" }
Write-Host "Already latest: $($current.Count)"
Write-Host "Failed:         $($failed.Count)"
foreach ($id in $failed) { Write-Host "  - $id" }

if ($updated.Count -gt 0) {
    Write-Host ""
    Write-Host "Restart Claude Code to apply updates."
}

if ($failed.Count -gt 0) { exit 1 } else { exit 0 }
