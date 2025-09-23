param(
    [string]$SourcePath = "training/output/vectors/",
    [string]$TargetPath = "app/vector-files/"
)

Write-Host "`n🔄 Updating vector files (Enhanced System)..." -ForegroundColor Green
Write-Host "🔍 Using SourcePath: $SourcePath"
Write-Host "📂 Using TargetPath: $TargetPath`n"

# Updated file names for enhanced system
$requiredFiles = @(
    "embeddings_enhanced.npy",
    "metadata_enhanced.pkl",
    "index_to_id_enhanced.pkl",
    "faiss_index_enhanced.index"
)

# Legacy file mappings (for backward compatibility)
$legacyMappings = @{
    "embeddings_enhanced.npy" = "embeddings_enhanced.npy"
    "metadata_enhanced" = "metadata_enhanced.pkl"
    "index_to_id_enhanced." = "index_to_id_enhanced.pkl"
}

Write-Host "`n🔍 Current Directory: $(Get-Location)" -ForegroundColor DarkGray
Write-Host "📦 Resolved SourcePath: $(Resolve-Path $SourcePath -ErrorAction SilentlyContinue)" -ForegroundColor Gray
Write-Host "📦 Resolved TargetPath: $(Resolve-Path -ErrorAction SilentlyContinue $TargetPath)" -ForegroundColor Gray

$missingFiles = @()
$foundFiles = @()

# Check for enhanced files first
foreach ($fileName in $requiredFiles) {
    $srcPath = Join-Path $SourcePath.TrimEnd('\') $fileName
    Write-Host "🔎 Checking enhanced: $srcPath" -ForegroundColor Cyan
    if (Test-Path $srcPath) {
        $foundFiles += @{source = $srcPath; target = $fileName; type = "enhanced"}
        Write-Host "✅ Found enhanced file: $fileName" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Enhanced file not found: $srcPath" -ForegroundColor Yellow
        $missingFiles += $fileName
    }
}

# Check for legacy files if enhanced not found
if ($missingFiles.Count -gt 0) {
    Write-Host "`n🔄 Checking for legacy files..." -ForegroundColor Yellow
    
    foreach ($legacyFile in $legacyMappings.Keys) {
        $srcPath = Join-Path $SourcePath.TrimEnd('\') $legacyFile
        $targetFile = $legacyMappings[$legacyFile]
        
        if ((Test-Path $srcPath) -and ($targetFile -in $missingFiles)) {
            Write-Host "✅ Found legacy file: $legacyFile -> $targetFile" -ForegroundColor Green
            $foundFiles += @{source = $srcPath; target = $targetFile; type = "legacy"}
            $missingFiles = $missingFiles | Where-Object { $_ -ne $targetFile }
        }
    }
}

if ($missingFiles.Count -gt 0) {
    Write-Host "`n🚫 Missing required files:" -ForegroundColor Red
    $missingFiles | ForEach-Object { Write-Host "   • $_" -ForegroundColor Red }
    Write-Host "`n💡 Expected files:" -ForegroundColor Yellow
    Write-Host "   Enhanced: embeddings_enhanced.npy, metadata_enhanced.pkl, index_to_id_enhanced.pkl, faiss_index_enhanced.index" -ForegroundColor Gray
    Write-Host "   OR Legacy: manual001_embeddings.npy, manual001_metadata.pkl, manual001_index_to_id.pkl" -ForegroundColor Gray
    exit 1
}

# Create target directory
if (-not (Test-Path $TargetPath)) {
    New-Item -ItemType Directory -Path $TargetPath -Force
    Write-Host "📁 Created directory: $TargetPath" -ForegroundColor Green
}

# Copy files
foreach ($fileInfo in $foundFiles) {
    $srcPath = $fileInfo.source
    $targetFileName = $fileInfo.target
    $fileType = $fileInfo.type
    $dstPath = Join-Path $TargetPath.TrimEnd('\') $targetFileName
    $backupPath = Join-Path $TargetPath.TrimEnd('\') "$targetFileName.backup"

    # Backup existing file
    if (Test-Path $dstPath) {
        Copy-Item $dstPath $backupPath -Force
        Write-Host "📋 Backed up: $targetFileName" -ForegroundColor Yellow
    }

    # Copy new file
    Copy-Item $srcPath $dstPath -Force
    $newSize = (Get-Item $dstPath).Length
    $sizeMB = [math]::Round($newSize/1MB, 2)
    
    if ($fileType -eq "legacy") {
        Write-Host "✅ Updated (legacy): $targetFileName ($sizeMB MB)" -ForegroundColor Orange
    } else {
        Write-Host "✅ Updated (enhanced): $targetFileName ($sizeMB MB)" -ForegroundColor Green
    }
}

Write-Host "`n✅ Vector files updated successfully!" -ForegroundColor Green
Write-Host "📊 System type: $(if($foundFiles | Where-Object {$_.type -eq 'enhanced'}) {'Enhanced RAG'} else {'Legacy'} )" -ForegroundColor Cyan

Write-Host "`n📝 Next steps:" -ForegroundColor Yellow
Write-Host "   1. Test locally: python main.py" -ForegroundColor White
Write-Host "   2. Deploy: .\deployment\deploy_ai_service.ps1" -ForegroundColor White
Write-Host "   3. Test: python deployment\test_ai_service.py" -ForegroundColor White