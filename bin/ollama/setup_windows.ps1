param()

$ErrorActionPreference = 'Stop'

function Write-Info($message, $color = 'Blue') {
    Write-Host $message -ForegroundColor $color
}

function Prompt-YesNo($message, $default = $true) {
    $suffix = if ($default) { '[Y/n]' } else { '[y/N]' }
    while ($true) {
        $response = Read-Host "$message $suffix"
        if ([string]::IsNullOrWhiteSpace($response)) {
            return $default
        }
        switch ($response.ToLowerInvariant()) {
            'y' { return $true }
            'yes' { return $true }
            'n' { return $false }
            'no' { return $false }
            default { Write-Host 'Please respond with y or n.' -ForegroundColor Yellow }
        }
    }
}

function Ensure-Directory($path) {
    if (-not (Test-Path $path)) {
        New-Item -ItemType Directory -Path $path | Out-Null
    }
}

function Resolve-EnvFile($path) {
    $expanded = [Environment]::ExpandEnvironmentVariables($path)
    $directory = Split-Path -Parent $expanded
    Ensure-Directory $directory
    if (-not (Test-Path $expanded)) {
        New-Item -ItemType File -Path $expanded -Force | Out-Null
    }
    return (Resolve-Path $expanded).Path
}

function Set-EnvValue($filePath, $key, $value) {
    $resolved = Resolve-EnvFile $filePath
    $lines = @()
    if (Test-Path $resolved) {
        $content = Get-Content -Path $resolved -ErrorAction SilentlyContinue
        if ($null -ne $content) {
            $lines = [System.Collections.Generic.List[string]]::new()
            foreach ($line in $content) {
                $lines.Add($line)
            }
        }
    }
    if ($lines.Count -eq 0) {
        $lines = [System.Collections.Generic.List[string]]::new()
    }

    $updated = $false
    for ($i = 0; $i -lt $lines.Count; $i++) {
        $line = $lines[$i]
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        $stripped = $line.TrimStart('#')
        if ($stripped.StartsWith("$key=")) {
            $lines[$i] = "$key=$value"
            $updated = $true
            break
        }
    }
    if (-not $updated) {
        $lines.Add("$key=$value")
    }

    $newline = [Environment]::NewLine
    Set-Content -Path $resolved -Value ($lines -join $newline) -Encoding UTF8
}

function Get-EmbeddingBaseFromLanguageBase($baseUrl) {
    if ([string]::IsNullOrWhiteSpace($baseUrl)) {
        return $null
    }
    $trimmed = $baseUrl.TrimEnd('/')
    if ($trimmed.EndsWith('/v1')) {
        $trimmed = $trimmed.Substring(0, $trimmed.Length - 3)
    }
    return $trimmed.TrimEnd('/')
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path (Join-Path $ScriptDir '..\..')).Path
$ProjectEnv = Join-Path $ProjectRoot '.env'
$UserEnvDir = Join-Path $env:USERPROFILE '.dana'
$UserEnv = Join-Path $UserEnvDir '.env'

function Ensure-OllamaInstalled {
    if (Get-Command ollama -ErrorAction SilentlyContinue) {
        return
    }

    Write-Info 'Ollama is not installed on this system.' 'Yellow'
    if (-not (Prompt-YesNo 'Would you like to install Ollama now?')) {
        throw 'Ollama is required for local setup. Aborting.'
    }

    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        throw 'winget is required to install Ollama automatically. Visit https://ollama.com/download to install manually, then rerun this script.'
    }

    Write-Info 'Installing Ollama via winget...' 'Blue'
    & winget install -e --id Ollama.Ollama -h --accept-package-agreements --accept-source-agreements
}

function Verify-Ollama {
    Ensure-OllamaInstalled
    $version = (& ollama --version 2>$null)
    if (-not $version) {
        throw "'ollama --version' did not return a version string. Please ensure Ollama is installed and available in PATH."
    }
    Write-Info "✅ Ollama detected: $version" 'Green'
    Write-Host
}

function Choose-EnvTargets {
    Write-Info 'Where should we store your Ollama settings?' 'Blue'
    Write-Host '  1) Project-only (.env in repository root) — keeps settings local to this project.'
    Write-Host '  2) User-wide (%USERPROFILE%\.dana\.env) — reuse across all Dana projects for this user.'
    Write-Host '  3) Both project and user scopes.'

    while ($true) {
        $choice = Read-Host 'Select an option (1-3)'
        switch ($choice) {
            '1' { return @($ProjectEnv) }
            '2' { return @($UserEnv) }
            '3' { return @($ProjectEnv, $UserEnv) }
        }
        Write-Host 'Please enter 1, 2, or 3.' -ForegroundColor Yellow
    }
}

function Choose-UsageMode {
    Write-Info 'How do you plan to use Ollama?' 'Blue'
    Write-Host '  1) Local language model only (chat, completions).'
    Write-Host '  2) Local embedding model only.'
    Write-Host '  3) Both language model and embeddings.'

    while ($true) {
        $choice = Read-Host 'Select an option (1-3)'
        switch ($choice) {
            '1' { return @{ lm = $true; embeddings = $false } }
            '2' { return @{ lm = $false; embeddings = $true } }
            '3' {
                Write-Host 'Configuring both. Language model setup will run first.' -ForegroundColor Yellow
                return @{ lm = $true; embeddings = $true }
            }
        }
        Write-Host 'Please enter 1, 2, or 3.' -ForegroundColor Yellow
    }
}

function Get-InstalledModels {
    $output = (& ollama list 2>$null)
    if (-not $output) { return @() }
    $models = @()
    $lines = $output -split "`n"
    for ($i = 1; $i -lt $lines.Length; $i++) {
        $line = $lines[$i].Trim()
        if ($line) {
            $model = ($line -split '\s+')[0]
            if ($model) { $models += $model }
        }
    }
    return $models
}

function Ensure-ModelPresent($model) {
    $models = Get-InstalledModels
    if ($models -contains $model) { return }
    Write-Info "Pulling model '$model' via ollama pull..." 'Yellow'
    & ollama pull $model
}

function Choose-LanguageModel {
    $installed = Get-InstalledModels
    if ($installed.Count -gt 0) {
        Write-Info 'Installed models detected:' 'Blue'
        for ($i = 0; $i -lt $installed.Count; $i++) {
            Write-Host "  $($i + 1)) $($installed[$i])"
        }
        Write-Host "  $($installed.Count + 1)) Choose from recommended list"
        Write-Host "  $($installed.Count + 2)) Enter a custom model name"

        while ($true) {
            $choice = Read-Host "Select an option (1-$($installed.Count + 2))"
            if ($choice -match '^[0-9]+$') {
                $index = [int]$choice
                if ($index -ge 1 -and $index -le $installed.Count) {
                    return $installed[$index - 1]
                } elseif ($index -eq $installed.Count + 1) {
                    break
                } elseif ($index -eq $installed.Count + 2) {
                    $custom = Read-Host 'Enter custom model name'
                    if (-not [string]::IsNullOrWhiteSpace($custom)) { return $custom }
                }
            }
            Write-Host 'Please choose a valid option.' -ForegroundColor Yellow
        }
    }

    Write-Info 'Recommended Ollama models:' 'Blue'
    Write-Host '  1) phi3:mini — speedy and lightweight'
    Write-Host '  2) llama3 — larger, needs 16+ GB RAM'
    Write-Host '  3) mistral — balanced general model'
    Write-Host '  4) qwen:4b — multilingual option'
    Write-Host '  5) Enter a different model'

    while ($true) {
        $choice = Read-Host 'Select a model (1-5)'
        switch ($choice) {
            '1' { return 'phi3:mini' }
            '2' { return 'llama3' }
            '3' { return 'mistral' }
            '4' { return 'qwen:4b' }
            '5' {
                $custom = Read-Host 'Enter custom model name'
                if (-not [string]::IsNullOrWhiteSpace($custom)) { return $custom }
            }
        }
        Write-Host 'Please choose a valid option.' -ForegroundColor Yellow
    }
}

function Configure-LanguageModel($envTargets) {
    Write-Info '--- Language model setup ---' 'Blue'
    $model = Choose-LanguageModel
    Ensure-ModelPresent $model

    $apiKey = Read-Host "LOCAL_API_KEY (Enter for 'no_key_needed')"
    if ([string]::IsNullOrWhiteSpace($apiKey)) { $apiKey = 'no_key_needed' }

    $defaultBase = 'http://localhost:11434/v1'
    $baseUrl = Read-Host "Base URL for OpenAI-compatible endpoint [$defaultBase]"
    if ([string]::IsNullOrWhiteSpace($baseUrl)) { $baseUrl = $defaultBase }

    foreach ($envPath in $envTargets) {
        Set-EnvValue $envPath 'LOCAL_API_KEY' $apiKey
        Set-EnvValue $envPath 'LOCAL_BASE_URL' $baseUrl
        Set-EnvValue $envPath 'LOCAL_MODEL_NAME' $model
    }

    Write-Info 'Language model configuration saved.' 'Green'
    return @{ Model = $model; ApiKey = $apiKey; BaseUrl = $baseUrl }
}

function Choose-EmbeddingModel {
    Write-Info 'Embedding model options:' 'Blue'
    Write-Host '  1) nomic-embed-text — fastest for smaller contexts'
    Write-Host '  2) mxbai-embed-large — higher quality, large contexts'
    Write-Host '  3) bge-m3 — great multilingual coverage'
    Write-Host '  4) Enter a different model'

    while ($true) {
        $choice = Read-Host 'Select an embedding model (1-4)'
        switch ($choice) {
            '1' { return @{ Model = 'nomic-embed-text'; Dimensions = 768 } }
            '2' { return @{ Model = 'mxbai-embed-large'; Dimensions = 1024 } }
            '3' { return @{ Model = 'bge-m3'; Dimensions = 1024 } }
            '4' {
                $custom = Read-Host 'Enter custom embedding model name'
                if (-not [string]::IsNullOrWhiteSpace($custom)) {
                    $dims = Read-Host 'Embedding dimensions (check the Ollama model page)'
                    if (-not [string]::IsNullOrWhiteSpace($dims)) {
                        return @{ Model = $custom; Dimensions = [int]$dims }
                    }
                    Write-Host 'Dimensions cannot be empty.' -ForegroundColor Yellow
                }
            }
        }
        Write-Host 'Please choose a valid option.' -ForegroundColor Yellow
    }
}

function Configure-Embeddings($envTargets, $languageContext) {
    Write-Info '--- Embedding setup ---' 'Blue'
    $selection = Choose-EmbeddingModel
    Ensure-ModelPresent $selection.Model

    $lmBase = $languageContext.BaseUrl
    $derivedBase = Get-EmbeddingBaseFromLanguageBase $lmBase
    if (-not $derivedBase) { $derivedBase = 'http://localhost:11434' }

    $baseUrl = Read-Host "Embedding base URL [$derivedBase]"
    if ([string]::IsNullOrWhiteSpace($baseUrl)) { $baseUrl = $derivedBase }

    $batchSize = Read-Host 'Embedding batch size (Enter for 32)'
    if ([string]::IsNullOrWhiteSpace($batchSize)) { $batchSize = '32' }

    foreach ($envPath in $envTargets) {
        Set-EnvValue $envPath 'LOCAL_EMBEDDING_BASE_URL' $baseUrl
        Set-EnvValue $envPath 'LOCAL_EMBEDDING_MODEL_NAME' $selection.Model
        Set-EnvValue $envPath 'EMBEDDING_DIMENSIONS' $selection.Dimensions
        Set-EnvValue $envPath 'EMBEDDING_BATCH_SIZE' $batchSize
    }

    Write-Info 'Embedding configuration saved.' 'Green'
    return @{ Model = $selection.Model; BaseUrl = $baseUrl; BatchSize = $batchSize; Dimensions = $selection.Dimensions }
}

function Test-LanguageModel($context) {
    Write-Info 'Testing language model via OpenAI-compatible endpoint...' 'Blue'
    $headers = @{ 'Content-Type' = 'application/json' }
    if ($context.ApiKey -and $context.ApiKey -ne 'no_key_needed') {
        $headers['Authorization'] = "Bearer $($context.ApiKey)"
    }

    $payload = @{
        model = $context.Model
        messages = @(@{ role = 'user'; content = 'Reply with the word ok.' })
        max_tokens = 5
    } | ConvertTo-Json -Depth 4

    $uri = "$($context.BaseUrl.TrimEnd('/'))/chat/completions"

    try {
        $response = Invoke-RestMethod -Uri $uri -Method Post -Headers $headers -Body $payload -TimeoutSec 30
        Write-Info '✅ Language model test succeeded.' 'Green'
    } catch {
        Write-Host '❌ Language model test failed.' -ForegroundColor Red
        Write-Host $_.Exception.Message
    }
}

function Test-Embeddings($context) {
    Write-Info 'Testing embedding endpoint...' 'Blue'
    $payload = @{
        model = $context.Model
        input = @('This is a quick Dana embedding test.')
    } | ConvertTo-Json -Depth 4

    $uri = "$($context.BaseUrl.TrimEnd('/'))/api/embed"

    try {
        $response = Invoke-RestMethod -Uri $uri -Method Post -Body $payload -ContentType 'application/json' -TimeoutSec 30
        Write-Info '✅ Embedding test succeeded.' 'Green'
    } catch {
        Write-Host '❌ Embedding test failed.' -ForegroundColor Red
        Write-Host $_.Exception.Message
    }
}

Verify-Ollama

$envTargets = Choose-EnvTargets
$usage = Choose-UsageMode
$lmContext = $null
$embedContext = $null

if ($usage.lm) {
    $lmContext = Configure-LanguageModel $envTargets
}

if ($usage.embeddings) {
    $embedContext = Configure-Embeddings $envTargets $lmContext
}

Write-Info 'Running validation checks...' 'Blue'
if ($usage.lm -and $lmContext) {
    Test-LanguageModel $lmContext
}
if ($usage.embeddings -and $embedContext) {
    Test-Embeddings $embedContext
}

Write-Host
Write-Info '🎉 Dana + Ollama setup complete!' 'Green'
Write-Info ("Updated environment file(s): {0}" -f (($envTargets | ForEach-Object { Resolve-EnvFile $_ }) -join ', ')) 'Green'
Write-Info 'Launch Dana with `dana-repl` and call set_model("local") to get started.' 'Blue'
